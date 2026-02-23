"""Tests for cclaw.orchestrator module."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from cclaw.orchestrator import (
    OrchestrationPlan,
    OrchestrationStep,
    StepResult,
    _build_plan_prompt,
    _inject_dependency_results,
    _parse_plan,
    create_plan,
    execute_plan,
    orchestrator_session_directory,
    run_orchestrated_task,
    summarize_results,
)

MOCK_RUN_CLAUDE = "cclaw.orchestrator.run_claude"
MOCK_LOAD_BOT_CONFIG = "cclaw.orchestrator.load_bot_config"
MOCK_BOT_DIRECTORY = "cclaw.orchestrator.bot_directory"
MOCK_SESSION_DIR = "cclaw.orchestrator.orchestrator_session_directory"


@pytest.fixture
def sample_plan():
    """Return a sample orchestration plan."""
    return OrchestrationPlan(
        task="적정 생활비를 찾아줘",
        steps=[
            OrchestrationStep(
                step_number=1,
                bot_name="butler",
                prompt="현재 생활 패턴과 소비 내역을 정리해주세요",
                depends_on=[],
            ),
            OrchestrationStep(
                step_number=2,
                bot_name="finance",
                prompt="아래 소비 내역 기반으로 적정 생활비를 분석해주세요. {step_1}",
                depends_on=[1],
            ),
        ],
        summary_prompt="모든 결과를 종합해 사용자에게 알려주세요",
    )


@pytest.fixture
def sample_plan_json():
    """Return the JSON that Claude would produce for the sample plan."""
    return json.dumps(
        {
            "steps": [
                {
                    "step_number": 1,
                    "bot_name": "butler",
                    "prompt": "현재 생활 패턴과 소비 내역을 정리해주세요",
                    "depends_on": [],
                },
                {
                    "step_number": 2,
                    "bot_name": "finance",
                    "prompt": "적정 생활비를 분석해주세요. {step_1}",
                    "depends_on": [1],
                },
            ],
            "summary_prompt": "결과를 종합해주세요",
        },
        ensure_ascii=False,
    )


# --- orchestrator_session_directory ---


def test_orchestrator_session_directory(tmp_path, monkeypatch):
    """orchestrator_session_directory creates and returns the directory."""
    monkeypatch.setenv("CCLAW_HOME", str(tmp_path))
    directory = orchestrator_session_directory()
    assert directory.exists()
    assert directory.name == "orchestrator_sessions"


# --- _build_plan_prompt ---


def test_build_plan_prompt():
    """_build_plan_prompt includes bot descriptions and task."""
    prompt = _build_plan_prompt(
        task="적정 생활비를 찾아줘",
        bot_descriptions={
            "butler": "집사 - 생활 관리",
            "finance": "재무사 - 재무 분석",
        },
    )
    assert "butler" in prompt
    assert "finance" in prompt
    assert "적정 생활비" in prompt
    assert "JSON" in prompt


# --- _parse_plan ---


def test_parse_plan_raw_json(sample_plan_json):
    """_parse_plan handles raw JSON."""
    plan = _parse_plan(sample_plan_json, "test task")
    assert len(plan.steps) == 2
    assert plan.steps[0].bot_name == "butler"
    assert plan.steps[1].depends_on == [1]
    assert plan.summary_prompt == "결과를 종합해주세요"
    assert plan.task == "test task"


def test_parse_plan_markdown_fenced(sample_plan_json):
    """_parse_plan handles markdown code blocks."""
    fenced = f"```json\n{sample_plan_json}\n```"
    plan = _parse_plan(fenced, "test task")
    assert len(plan.steps) == 2


def test_parse_plan_generic_fence(sample_plan_json):
    """_parse_plan handles generic ``` code blocks."""
    fenced = f"```\n{sample_plan_json}\n```"
    plan = _parse_plan(fenced, "test task")
    assert len(plan.steps) == 2


def test_parse_plan_invalid_json():
    """_parse_plan raises ValueError for invalid JSON."""
    with pytest.raises(ValueError, match="Invalid JSON"):
        _parse_plan("not json at all", "task")


def test_parse_plan_empty_steps():
    """_parse_plan raises ValueError when steps list is empty."""
    with pytest.raises(ValueError, match="at least one step"):
        _parse_plan('{"steps": []}', "task")


def test_parse_plan_no_steps_key():
    """_parse_plan raises ValueError when steps key is missing."""
    with pytest.raises((ValueError, KeyError)):
        _parse_plan('{"something": "else"}', "task")


# --- _inject_dependency_results ---


def test_inject_dependency_with_placeholder():
    """Placeholder {step_N} is replaced with the dependency result."""
    step = OrchestrationStep(
        step_number=2,
        bot_name="finance",
        prompt="분석해주세요: {step_1}",
        depends_on=[1],
    )
    results = {
        1: StepResult(step_number=1, bot_name="butler", response="월 200만원 소비"),
    }
    prompt = _inject_dependency_results(step, results)
    assert "월 200만원 소비" in prompt
    assert "{step_1}" not in prompt


def test_inject_dependency_without_placeholder():
    """When no placeholder exists, context is prepended."""
    step = OrchestrationStep(
        step_number=2,
        bot_name="finance",
        prompt="적정 생활비를 분석해주세요",
        depends_on=[1],
    )
    results = {
        1: StepResult(step_number=1, bot_name="butler", response="월 200만원 소비"),
    }
    prompt = _inject_dependency_results(step, results)
    assert "이전 단계 결과를 참고하세요" in prompt
    assert "월 200만원 소비" in prompt
    assert "적정 생활비를 분석해주세요" in prompt


def test_inject_dependency_no_dependencies():
    """Steps without dependencies return the original prompt."""
    step = OrchestrationStep(
        step_number=1,
        bot_name="butler",
        prompt="소비 내역을 정리해주세요",
        depends_on=[],
    )
    prompt = _inject_dependency_results(step, {})
    assert prompt == "소비 내역을 정리해주세요"


def test_inject_multiple_dependencies():
    """Multiple dependency placeholders are all replaced."""
    step = OrchestrationStep(
        step_number=3,
        bot_name="analyst",
        prompt="Step 1: {step_1}\nStep 2: {step_2}",
        depends_on=[1, 2],
    )
    results = {
        1: StepResult(step_number=1, bot_name="butler", response="data A"),
        2: StepResult(step_number=2, bot_name="finance", response="data B"),
    }
    prompt = _inject_dependency_results(step, results)
    assert "data A" in prompt
    assert "data B" in prompt
    assert "{step_1}" not in prompt
    assert "{step_2}" not in prompt


# --- create_plan ---


@pytest.mark.asyncio
async def test_create_plan_success(tmp_path, monkeypatch, sample_plan_json):
    """create_plan returns a valid plan."""
    monkeypatch.setenv("CCLAW_HOME", str(tmp_path))

    with (
        patch(MOCK_LOAD_BOT_CONFIG) as mock_config,
        patch(MOCK_RUN_CLAUDE, new_callable=AsyncMock) as mock_claude,
    ):
        mock_config.side_effect = lambda name: {
            "butler": {"personality": "집사", "description": "생활 관리"},
            "finance": {"personality": "재무사", "description": "재무 분석"},
        }.get(name)
        mock_claude.return_value = sample_plan_json

        plan = await create_plan("적정 생활비", ["butler", "finance"])

    assert len(plan.steps) == 2
    assert plan.steps[0].bot_name == "butler"
    assert plan.steps[1].bot_name == "finance"


@pytest.mark.asyncio
async def test_create_plan_bot_not_found(tmp_path, monkeypatch):
    """create_plan raises ValueError for unknown bots."""
    monkeypatch.setenv("CCLAW_HOME", str(tmp_path))

    with patch(MOCK_LOAD_BOT_CONFIG, return_value=None):
        with pytest.raises(ValueError, match="not found"):
            await create_plan("task", ["nonexistent"])


@pytest.mark.asyncio
async def test_create_plan_validates_referenced_bots(tmp_path, monkeypatch):
    """create_plan rejects plans that reference bots not in the request."""
    monkeypatch.setenv("CCLAW_HOME", str(tmp_path))

    bad_plan = json.dumps(
        {
            "steps": [
                {
                    "step_number": 1,
                    "bot_name": "unknown_bot",
                    "prompt": "do something",
                    "depends_on": [],
                }
            ],
            "summary_prompt": "",
        }
    )

    with (
        patch(MOCK_LOAD_BOT_CONFIG) as mock_config,
        patch(MOCK_RUN_CLAUDE, new_callable=AsyncMock) as mock_claude,
    ):
        mock_config.return_value = {"personality": "test", "description": "test"}
        mock_claude.return_value = bad_plan

        with pytest.raises(ValueError, match="unknown bot"):
            await create_plan("task", ["butler"])


# --- execute_plan ---


@pytest.mark.asyncio
async def test_execute_plan_runs_steps(tmp_path, sample_plan):
    """execute_plan runs each step and returns results."""
    with (
        patch(MOCK_LOAD_BOT_CONFIG) as mock_config,
        patch(MOCK_BOT_DIRECTORY, return_value=tmp_path),
        patch(MOCK_RUN_CLAUDE, new_callable=AsyncMock) as mock_claude,
    ):
        mock_config.return_value = {"model": "sonnet", "skills": []}
        mock_claude.side_effect = ["소비 내역: 월 200만원", "적정 생활비: 월 180만원"]

        results = await execute_plan(sample_plan)

    assert len(results) == 2
    assert results[0].bot_name == "butler"
    assert "소비 내역" in results[0].response
    assert results[1].bot_name == "finance"
    assert "적정 생활비" in results[1].response


@pytest.mark.asyncio
async def test_execute_plan_injects_dependencies(tmp_path, sample_plan):
    """execute_plan injects step 1 result into step 2 prompt."""
    prompts_received = []

    async def capture_run_claude(working_directory, message, **kwargs):
        prompts_received.append(message)
        if len(prompts_received) == 1:
            return "월 200만원 소비"
        return "분석 완료"

    with (
        patch(MOCK_LOAD_BOT_CONFIG) as mock_config,
        patch(MOCK_BOT_DIRECTORY, return_value=tmp_path),
        patch(MOCK_RUN_CLAUDE, side_effect=capture_run_claude),
    ):
        mock_config.return_value = {"model": "sonnet", "skills": []}
        await execute_plan(sample_plan)

    # Step 2's prompt should contain step 1's result (placeholder replaced)
    assert "월 200만원 소비" in prompts_received[1]


@pytest.mark.asyncio
async def test_execute_plan_callbacks(tmp_path, sample_plan):
    """execute_plan fires on_step_start and on_step_complete callbacks."""
    started = []
    completed = []

    async def on_start(step):
        started.append(step.step_number)

    async def on_complete(result):
        completed.append(result.step_number)

    with (
        patch(MOCK_LOAD_BOT_CONFIG) as mock_config,
        patch(MOCK_BOT_DIRECTORY, return_value=tmp_path),
        patch(MOCK_RUN_CLAUDE, new_callable=AsyncMock, return_value="response"),
    ):
        mock_config.return_value = {"model": "sonnet", "skills": []}
        await execute_plan(sample_plan, on_step_start=on_start, on_step_complete=on_complete)

    assert started == [1, 2]
    assert completed == [1, 2]


@pytest.mark.asyncio
async def test_execute_plan_bot_not_found(sample_plan):
    """execute_plan raises ValueError if a step's bot doesn't exist."""
    with patch(MOCK_LOAD_BOT_CONFIG, return_value=None):
        with pytest.raises(ValueError, match="not found"):
            await execute_plan(sample_plan)


# --- summarize_results ---


@pytest.mark.asyncio
async def test_summarize_results_without_summary_prompt():
    """summarize_results concatenates results when no summary_prompt."""
    plan = OrchestrationPlan(task="test", steps=[], summary_prompt="")
    results = [
        StepResult(step_number=1, bot_name="butler", response="result A"),
        StepResult(step_number=2, bot_name="finance", response="result B"),
    ]
    summary = await summarize_results(plan, results)
    assert "butler" in summary
    assert "finance" in summary
    assert "result A" in summary
    assert "result B" in summary


@pytest.mark.asyncio
async def test_summarize_results_with_summary_prompt(tmp_path, monkeypatch):
    """summarize_results uses Claude when summary_prompt is provided."""
    monkeypatch.setenv("CCLAW_HOME", str(tmp_path))

    plan = OrchestrationPlan(
        task="test",
        steps=[],
        summary_prompt="종합해주세요",
    )
    results = [
        StepResult(step_number=1, bot_name="butler", response="result A"),
    ]

    with patch(MOCK_RUN_CLAUDE, new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = "종합 결과입니다"
        summary = await summarize_results(plan, results)

    assert summary == "종합 결과입니다"
    # Verify the prompt includes the original task and results
    call_prompt = mock_claude.call_args[1]["message"]
    assert "test" in call_prompt
    assert "result A" in call_prompt
    assert "종합해주세요" in call_prompt


# --- run_orchestrated_task ---


@pytest.mark.asyncio
async def test_run_orchestrated_task_end_to_end(tmp_path, monkeypatch, sample_plan_json):
    """run_orchestrated_task runs the full pipeline."""
    monkeypatch.setenv("CCLAW_HOME", str(tmp_path))

    call_count = 0

    async def mock_run(working_directory, message, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # Planning phase
            return sample_plan_json
        elif call_count == 2:
            return "소비 내역: 월 200만원"
        elif call_count == 3:
            return "적정 생활비: 월 180만원"
        else:
            return "종합 결과"

    with (
        patch(MOCK_LOAD_BOT_CONFIG) as mock_config,
        patch(MOCK_BOT_DIRECTORY, return_value=tmp_path),
        patch(MOCK_RUN_CLAUDE, side_effect=mock_run),
    ):
        mock_config.side_effect = lambda name: {
            "butler": {"personality": "집사", "description": "생활 관리", "model": "sonnet", "skills": []},
            "finance": {"personality": "재무사", "description": "재무 분석", "model": "sonnet", "skills": []},
        }.get(name)

        result = await run_orchestrated_task(
            task="적정 생활비",
            bot_names=["butler", "finance"],
        )

    # 4 calls: plan + step1 + step2 + summary
    assert call_count == 4
    assert "종합 결과" in result
