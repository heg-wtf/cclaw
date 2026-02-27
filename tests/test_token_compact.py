"""Tests for cclaw.token_compact module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import yaml

from cclaw.token_compact import (
    DOCUMENT_TYPE_HEARTBEAT,
    DOCUMENT_TYPE_MEMORY,
    DOCUMENT_TYPE_SKILL,
    CompactResult,
    CompactTarget,
    collect_compact_targets,
    compact_content,
    estimate_token_count,
    format_compact_report,
    run_compact,
    save_compact_results,
)


@pytest.fixture
def temp_cclaw_home(tmp_path, monkeypatch):
    """Set CCLAW_HOME to a temporary directory."""
    home = tmp_path / ".cclaw"
    monkeypatch.setenv("CCLAW_HOME", str(home))
    return home


@pytest.fixture
def setup_bot(temp_cclaw_home):
    """Create a minimal bot structure."""
    bot_path = temp_cclaw_home / "bots" / "test-bot"
    bot_path.mkdir(parents=True)
    (bot_path / "sessions").mkdir()
    bot_config = {
        "token": "fake-token",
        "personality": "helpful",
        "description": "test bot",
        "model": "sonnet",
        "skills": [],
    }
    with open(bot_path / "bot.yaml", "w") as file:
        yaml.dump(bot_config, file)
    return bot_path


@pytest.fixture
def setup_bot_with_memory(setup_bot):
    """Create a bot with MEMORY.md."""
    memory_content = "# Memory\n\n- User likes coffee\n- Timezone: Asia/Seoul\n"
    (setup_bot / "MEMORY.md").write_text(memory_content)
    return setup_bot


@pytest.fixture
def setup_bot_with_skill(setup_bot, temp_cclaw_home):
    """Create a bot with a user-created skill attached."""
    # Create the skill
    skill_path = temp_cclaw_home / "skills" / "my-skill"
    skill_path.mkdir(parents=True)
    (skill_path / "SKILL.md").write_text("# my-skill\n\nDo something useful.\n")

    # Attach to bot
    bot_yaml_path = setup_bot / "bot.yaml"
    with open(bot_yaml_path) as file:
        config = yaml.safe_load(file)
    config["skills"] = ["my-skill"]
    with open(bot_yaml_path, "w") as file:
        yaml.dump(config, file)

    return setup_bot


@pytest.fixture
def setup_bot_with_heartbeat(setup_bot):
    """Create a bot with HEARTBEAT.md."""
    heartbeat_directory = setup_bot / "heartbeat_sessions"
    heartbeat_directory.mkdir(parents=True)
    (heartbeat_directory / "HEARTBEAT.md").write_text("# Heartbeat\n\n- [ ] Check API status\n")
    return setup_bot


# --- estimate_token_count ---


class TestEstimateTokenCount:
    def test_empty_string(self):
        assert estimate_token_count("") == 1

    def test_short_string(self):
        assert estimate_token_count("hi") == 1

    def test_normal_string(self):
        text = "a" * 100
        assert estimate_token_count(text) == 25

    def test_long_string(self):
        text = "a" * 4000
        assert estimate_token_count(text) == 1000


# --- collect_compact_targets ---


class TestCollectCompactTargets:
    def test_no_bot_config(self, temp_cclaw_home):
        targets = collect_compact_targets("nonexistent")
        assert targets == []

    def test_no_targets(self, setup_bot):
        targets = collect_compact_targets("test-bot")
        assert targets == []

    def test_memory_only(self, setup_bot_with_memory):
        targets = collect_compact_targets("test-bot")
        assert len(targets) == 1
        assert targets[0].label == "MEMORY.md"
        assert targets[0].document_type == DOCUMENT_TYPE_MEMORY
        assert "coffee" in targets[0].content

    def test_empty_memory_skipped(self, setup_bot):
        (setup_bot / "MEMORY.md").write_text("   \n  \n  ")
        targets = collect_compact_targets("test-bot")
        assert targets == []

    def test_user_skill_included(self, setup_bot_with_skill):
        targets = collect_compact_targets("test-bot")
        assert len(targets) == 1
        assert targets[0].label == "Skill: my-skill"
        assert targets[0].document_type == DOCUMENT_TYPE_SKILL

    def test_builtin_skill_excluded(self, setup_bot, temp_cclaw_home):
        """Builtin skills should not be collected as compact targets."""
        # Attach a builtin skill name to bot
        bot_yaml_path = setup_bot / "bot.yaml"
        with open(bot_yaml_path) as file:
            config = yaml.safe_load(file)
        config["skills"] = ["imessage"]
        with open(bot_yaml_path, "w") as file:
            yaml.dump(config, file)

        targets = collect_compact_targets("test-bot")
        # imessage is a builtin, should be excluded
        assert len(targets) == 0

    def test_heartbeat_included(self, setup_bot_with_heartbeat):
        targets = collect_compact_targets("test-bot")
        assert len(targets) == 1
        assert targets[0].label == "HEARTBEAT.md"
        assert targets[0].document_type == DOCUMENT_TYPE_HEARTBEAT

    def test_all_targets(self, setup_bot_with_memory, temp_cclaw_home):
        """Test collecting all three target types."""
        bot_path = setup_bot_with_memory

        # Add skill
        skill_path = temp_cclaw_home / "skills" / "custom-skill"
        skill_path.mkdir(parents=True)
        (skill_path / "SKILL.md").write_text("# custom\n\nInstructions.\n")
        bot_yaml_path = bot_path / "bot.yaml"
        with open(bot_yaml_path) as file:
            config = yaml.safe_load(file)
        config["skills"] = ["custom-skill"]
        with open(bot_yaml_path, "w") as file:
            yaml.dump(config, file)

        # Add heartbeat
        heartbeat_directory = bot_path / "heartbeat_sessions"
        heartbeat_directory.mkdir(parents=True)
        (heartbeat_directory / "HEARTBEAT.md").write_text("# HB\n\n- Check\n")

        targets = collect_compact_targets("test-bot")
        assert len(targets) == 3
        labels = [t.label for t in targets]
        assert "MEMORY.md" in labels
        assert "Skill: custom-skill" in labels
        assert "HEARTBEAT.md" in labels


# --- compact_content ---


class TestCompactContent:
    @pytest.mark.asyncio
    async def test_calls_run_claude(self):
        with patch("cclaw.claude_runner.run_claude", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = "compressed output"

            result = await compact_content(
                content="some long content",
                document_type="test doc",
                working_directory="/tmp/test",
                model="sonnet",
            )

            assert result == "compressed output"
            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args
            assert call_kwargs.kwargs["working_directory"] == "/tmp/test"
            assert call_kwargs.kwargs["model"] == "sonnet"
            assert "test doc" in call_kwargs.kwargs["message"]
            assert "some long content" in call_kwargs.kwargs["message"]

    @pytest.mark.asyncio
    async def test_strips_result(self):
        with patch("cclaw.claude_runner.run_claude", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = "  result with whitespace  \n\n"

            result = await compact_content(
                content="input",
                document_type="test",
                working_directory="/tmp/test",
            )

            assert result == "result with whitespace"


# --- CompactResult ---


class TestCompactResult:
    def test_savings_percentage(self):
        target = CompactTarget(
            label="test",
            file_path=Path("/tmp/test"),
            content="a" * 400,
            line_count=10,
            token_count=100,
            document_type="test",
        )
        result = CompactResult(
            target=target,
            compacted_content="a" * 280,
            compacted_lines=7,
            compacted_tokens=70,
        )
        assert result.savings_percentage == 30.0

    def test_savings_percentage_zero_tokens(self):
        target = CompactTarget(
            label="test",
            file_path=Path("/tmp/test"),
            content="",
            line_count=0,
            token_count=0,
            document_type="test",
        )
        result = CompactResult(target=target, compacted_tokens=0)
        assert result.savings_percentage == 0.0

    def test_savings_percentage_no_savings(self):
        target = CompactTarget(
            label="test",
            file_path=Path("/tmp/test"),
            content="a" * 100,
            line_count=5,
            token_count=25,
            document_type="test",
        )
        result = CompactResult(
            target=target,
            compacted_content="a" * 100,
            compacted_lines=5,
            compacted_tokens=25,
        )
        assert result.savings_percentage == 0.0


# --- run_compact ---


class TestRunCompact:
    @pytest.mark.asyncio
    async def test_full_flow(self, setup_bot_with_memory):
        with patch("cclaw.claude_runner.run_claude", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = "# Memory\n\n- Coffee lover\n"

            results = await run_compact("test-bot", model="sonnet")

            assert len(results) == 1
            assert results[0].error is None
            assert results[0].compacted_content == "# Memory\n\n- Coffee lover"
            assert results[0].compacted_lines == 3

    @pytest.mark.asyncio
    async def test_individual_failure_continues(self, setup_bot_with_memory, temp_cclaw_home):
        """When one target fails, remaining targets should still be processed."""
        # Add a skill so we have 2 targets
        skill_path = temp_cclaw_home / "skills" / "fail-skill"
        skill_path.mkdir(parents=True)
        (skill_path / "SKILL.md").write_text("# fail\n\nContent.\n")
        bot_yaml_path = setup_bot_with_memory / "bot.yaml"
        with open(bot_yaml_path) as file:
            config = yaml.safe_load(file)
        config["skills"] = ["fail-skill"]
        with open(bot_yaml_path, "w") as file:
            yaml.dump(config, file)

        call_count = 0

        async def mock_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "compacted memory"
            raise RuntimeError("Claude failed")

        with patch("cclaw.claude_runner.run_claude", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = mock_side_effect

            results = await run_compact("test-bot")

            assert len(results) == 2
            assert results[0].error is None
            assert results[1].error is not None
            assert "Claude failed" in results[1].error

    @pytest.mark.asyncio
    async def test_no_targets(self, setup_bot):
        results = await run_compact("test-bot")
        assert results == []


# --- format_compact_report ---


class TestFormatCompactReport:
    def test_normal_report(self):
        target = CompactTarget(
            label="MEMORY.md",
            file_path=Path("/tmp/test"),
            content="a" * 4800,
            line_count=45,
            token_count=1200,
            document_type=DOCUMENT_TYPE_MEMORY,
        )
        result = CompactResult(
            target=target,
            compacted_content="a" * 3120,
            compacted_lines=28,
            compacted_tokens=780,
        )
        report = format_compact_report("my-bot", [result])
        assert "my-bot" in report
        assert "MEMORY.md" in report
        assert "45 lines" in report
        assert "28 lines" in report
        assert "1,200 tokens" in report
        assert "780 tokens" in report
        assert "420 tokens" in report
        assert "35%" in report

    def test_error_report(self):
        target = CompactTarget(
            label="MEMORY.md",
            file_path=Path("/tmp/test"),
            content="content",
            line_count=1,
            token_count=2,
            document_type=DOCUMENT_TYPE_MEMORY,
        )
        result = CompactResult(target=target, error="something went wrong")
        report = format_compact_report("my-bot", [result])
        assert "something went wrong" in report
        assert "\u274c" in report

    def test_zero_savings(self):
        target = CompactTarget(
            label="MEMORY.md",
            file_path=Path("/tmp/test"),
            content="a" * 100,
            line_count=5,
            token_count=25,
            document_type=DOCUMENT_TYPE_MEMORY,
        )
        result = CompactResult(
            target=target,
            compacted_content="a" * 100,
            compacted_lines=5,
            compacted_tokens=25,
        )
        report = format_compact_report("my-bot", [result])
        assert "0%" in report
        assert "0 tokens" in report

    def test_empty_results(self):
        report = format_compact_report("my-bot", [])
        assert "Total saved: 0 tokens" in report


# --- save_compact_results ---


class TestSaveCompactResults:
    def test_saves_successful_results(self, tmp_path):
        file_path = tmp_path / "MEMORY.md"
        file_path.write_text("original content")

        target = CompactTarget(
            label="MEMORY.md",
            file_path=file_path,
            content="original content",
            line_count=1,
            token_count=4,
            document_type=DOCUMENT_TYPE_MEMORY,
        )
        result = CompactResult(
            target=target,
            compacted_content="compact content",
            compacted_lines=1,
            compacted_tokens=3,
        )

        save_compact_results([result])

        assert file_path.read_text() == "compact content"

    def test_skips_error_results(self, tmp_path):
        file_path = tmp_path / "MEMORY.md"
        file_path.write_text("original content")

        target = CompactTarget(
            label="MEMORY.md",
            file_path=file_path,
            content="original content",
            line_count=1,
            token_count=4,
            document_type=DOCUMENT_TYPE_MEMORY,
        )
        result = CompactResult(target=target, error="failed")

        save_compact_results([result])

        # File should remain unchanged
        assert file_path.read_text() == "original content"

    def test_mixed_results(self, tmp_path):
        good_path = tmp_path / "good.md"
        good_path.write_text("original good")
        bad_path = tmp_path / "bad.md"
        bad_path.write_text("original bad")

        good_target = CompactTarget(
            label="good",
            file_path=good_path,
            content="original good",
            line_count=1,
            token_count=3,
            document_type=DOCUMENT_TYPE_MEMORY,
        )
        bad_target = CompactTarget(
            label="bad",
            file_path=bad_path,
            content="original bad",
            line_count=1,
            token_count=3,
            document_type=DOCUMENT_TYPE_MEMORY,
        )

        results = [
            CompactResult(
                target=good_target,
                compacted_content="compact good",
                compacted_lines=1,
                compacted_tokens=3,
            ),
            CompactResult(target=bad_target, error="failed"),
        ]

        save_compact_results(results)

        assert good_path.read_text() == "compact good"
        assert bad_path.read_text() == "original bad"
