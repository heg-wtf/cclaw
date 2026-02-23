"""Multi-bot orchestration for cclaw."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable

from cclaw.claude_runner import run_claude
from cclaw.config import DEFAULT_MODEL, bot_directory, cclaw_home, load_bot_config

logger = logging.getLogger(__name__)


def orchestrator_session_directory() -> Path:
    """Return the orchestrator session directory (~/.cclaw/orchestrator_sessions/)."""
    directory = cclaw_home() / "orchestrator_sessions"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


@dataclass
class OrchestrationStep:
    """A single step in an orchestration plan."""

    step_number: int
    bot_name: str
    prompt: str
    depends_on: list[int] = field(default_factory=list)


@dataclass
class OrchestrationPlan:
    """An orchestration plan with ordered steps."""

    task: str
    steps: list[OrchestrationStep]
    summary_prompt: str = ""


@dataclass
class StepResult:
    """Result from executing a single step."""

    step_number: int
    bot_name: str
    response: str


def _build_plan_prompt(task: str, bot_descriptions: dict[str, str]) -> str:
    """Build the prompt for plan generation."""
    bot_info = "\n".join(f"- {name}: {desc}" for name, desc in bot_descriptions.items())

    return f"""다음 작업을 여러 봇이 협력해서 수행하기 위한 실행 계획을 JSON으로 만들어주세요.

## 사용 가능한 봇
{bot_info}

## 작업
{task}

## 응답 형식
정확히 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요.

```json
{{
  "steps": [
    {{
      "step_number": 1,
      "bot_name": "봇이름",
      "prompt": "이 봇에게 보낼 구체적인 지시",
      "depends_on": []
    }},
    {{
      "step_number": 2,
      "bot_name": "다른봇",
      "prompt": "이전 단계 결과를 참고해서 지시. {{step_1}} 자리에 1단계 결과가 삽입됩니다.",
      "depends_on": [1]
    }}
  ],
  "summary_prompt": "모든 단계 결과를 종합해 사용자에게 전달할 최종 요약 지시"
}}
```"""


def _parse_plan(raw_response: str, task: str) -> OrchestrationPlan:
    """Parse the plan JSON from Claude's response.

    Handles raw JSON and markdown-fenced code blocks.

    Raises:
        ValueError: If the JSON cannot be parsed.
    """
    response = raw_response.strip()

    # Extract JSON from markdown code blocks
    if "```json" in response:
        start = response.index("```json") + 7
        end = response.index("```", start)
        response = response[start:end].strip()
    elif "```" in response:
        start = response.index("```") + 3
        end = response.index("```", start)
        response = response[start:end].strip()

    try:
        data = json.loads(response)
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in plan response: {error}") from error

    if "steps" not in data or not data["steps"]:
        raise ValueError("Plan must contain at least one step")

    steps = []
    for step_data in data["steps"]:
        steps.append(
            OrchestrationStep(
                step_number=step_data["step_number"],
                bot_name=step_data["bot_name"],
                prompt=step_data["prompt"],
                depends_on=step_data.get("depends_on", []),
            )
        )

    return OrchestrationPlan(
        task=task,
        steps=steps,
        summary_prompt=data.get("summary_prompt", ""),
    )


async def create_plan(
    task: str,
    bot_names: list[str],
    model: str = DEFAULT_MODEL,
    timeout: int = 120,
) -> OrchestrationPlan:
    """Use Claude to create an orchestration plan.

    Args:
        task: The task description.
        bot_names: List of bot names to involve.
        model: Model to use for planning.
        timeout: Timeout for the planning step.

    Returns:
        An OrchestrationPlan with steps for each bot.

    Raises:
        ValueError: If the plan cannot be parsed or a bot is not found.
        RuntimeError: If Claude Code fails.
    """
    bot_descriptions: dict[str, str] = {}
    for name in bot_names:
        config = load_bot_config(name)
        if not config:
            raise ValueError(f"Bot '{name}' not found")
        personality = config.get("personality", "")
        description = config.get("description", "")
        bot_descriptions[name] = f"{personality} - {description}"

    prompt = _build_plan_prompt(task, bot_descriptions)
    working_dir = str(orchestrator_session_directory())

    response = await run_claude(
        working_directory=working_dir,
        message=prompt,
        timeout=timeout,
        model=model,
    )

    plan = _parse_plan(response, task)

    # Validate that all referenced bots exist in the requested list
    for step in plan.steps:
        if step.bot_name not in bot_names:
            raise ValueError(
                f"Plan references unknown bot '{step.bot_name}'. "
                f"Available: {', '.join(bot_names)}"
            )

    return plan


def _inject_dependency_results(
    step: OrchestrationStep,
    results: dict[int, StepResult],
) -> str:
    """Build the step prompt with dependency results injected.

    Replaces {step_N} placeholders. If the original prompt has dependencies
    but no placeholders, prepends context from previous steps.
    """
    prompt = step.prompt

    # Replace explicit placeholders
    for dep_number in step.depends_on:
        if dep_number in results:
            placeholder = f"{{step_{dep_number}}}"
            prompt = prompt.replace(placeholder, results[dep_number].response)

    # If dependencies exist but no placeholder was used, prepend context
    has_placeholder = any(f"{{step_{d}}}" in step.prompt for d in step.depends_on)
    if step.depends_on and not has_placeholder:
        context_parts = []
        for dep_number in step.depends_on:
            if dep_number in results:
                context_parts.append(
                    f"[Step {dep_number} - {results[dep_number].bot_name} 결과]\n"
                    f"{results[dep_number].response}"
                )
        if context_parts:
            context = "\n\n".join(context_parts)
            prompt = f"이전 단계 결과를 참고하세요:\n\n{context}\n\n---\n\n{prompt}"

    return prompt


async def execute_plan(
    plan: OrchestrationPlan,
    on_step_start: Callable[[OrchestrationStep], Awaitable[None]] | None = None,
    on_step_complete: Callable[[StepResult], Awaitable[None]] | None = None,
    timeout: int = 300,
) -> list[StepResult]:
    """Execute an orchestration plan step by step.

    Each step runs in the target bot's directory, using the bot's model and
    skills. Dependency results are injected into subsequent step prompts.

    Args:
        plan: The plan to execute.
        on_step_start: Async callback fired before each step.
        on_step_complete: Async callback fired after each step.
        timeout: Timeout per step in seconds.

    Returns:
        List of StepResults in execution order.
    """
    results: dict[int, StepResult] = {}

    for step in plan.steps:
        if on_step_start:
            await on_step_start(step)

        bot_config = load_bot_config(step.bot_name)
        if not bot_config:
            raise ValueError(f"Bot '{step.bot_name}' not found")

        model = bot_config.get("model", DEFAULT_MODEL)
        skills = bot_config.get("skills", [])
        bot_path = bot_directory(step.bot_name)

        prompt = _inject_dependency_results(step, results)

        response = await run_claude(
            working_directory=str(bot_path),
            message=prompt,
            timeout=timeout,
            model=model,
            skill_names=skills if skills else None,
        )

        result = StepResult(
            step_number=step.step_number,
            bot_name=step.bot_name,
            response=response,
        )
        results[step.step_number] = result

        if on_step_complete:
            await on_step_complete(result)

    return list(results.values())


async def summarize_results(
    plan: OrchestrationPlan,
    results: list[StepResult],
    model: str = DEFAULT_MODEL,
    timeout: int = 120,
) -> str:
    """Generate a summary of all orchestration results.

    If the plan includes a summary_prompt, Claude is used to synthesize
    the final output. Otherwise, step results are concatenated directly.

    Args:
        plan: The original plan.
        results: Step results to summarize.
        model: Model to use for summary generation.
        timeout: Timeout for summarization.

    Returns:
        The summary text.
    """
    if not plan.summary_prompt:
        parts = []
        for result in results:
            parts.append(
                f"## {result.bot_name} (Step {result.step_number})\n\n{result.response}"
            )
        return "\n\n---\n\n".join(parts)

    result_context = ""
    for result in results:
        result_context += (
            f"\n\n[{result.bot_name} (Step {result.step_number})]\n{result.response}"
        )

    prompt = (
        f"다음은 여러 봇이 협력하여 수행한 결과입니다.\n\n"
        f"## 원래 작업\n{plan.task}\n\n"
        f"## 각 봇의 결과\n{result_context}\n\n"
        f"## 요약 지시\n{plan.summary_prompt}"
    )

    working_dir = str(orchestrator_session_directory())
    return await run_claude(
        working_directory=working_dir,
        message=prompt,
        timeout=timeout,
        model=model,
    )


async def run_orchestrated_task(
    task: str,
    bot_names: list[str],
    model: str = DEFAULT_MODEL,
    on_step_start: Callable[[OrchestrationStep], Awaitable[None]] | None = None,
    on_step_complete: Callable[[StepResult], Awaitable[None]] | None = None,
    plan_timeout: int = 120,
    step_timeout: int = 300,
) -> str:
    """Run a full orchestrated multi-bot task.

    This is the main entry point for multi-bot orchestration:
    1. Creates an execution plan using Claude
    2. Executes each step against the appropriate bot
    3. Summarizes the combined results

    Args:
        task: The task description.
        bot_names: List of bot names to collaborate.
        model: Model to use for planning and summary.
        on_step_start: Optional callback fired before each step.
        on_step_complete: Optional callback fired after each step.
        plan_timeout: Timeout for the planning phase.
        step_timeout: Timeout per execution step.

    Returns:
        The final summary text.
    """
    plan = await create_plan(task, bot_names, model=model, timeout=plan_timeout)

    logger.info(
        "Orchestration plan created: %d steps for task '%s'",
        len(plan.steps),
        task[:100],
    )

    results = await execute_plan(
        plan,
        on_step_start=on_step_start,
        on_step_complete=on_step_complete,
        timeout=step_timeout,
    )

    summary = await summarize_results(plan, results, model=model)
    return summary
