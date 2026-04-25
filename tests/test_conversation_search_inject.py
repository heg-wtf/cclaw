"""Tests for conversation_search auto-injection into Claude Code config."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def session_dir(tmp_path: Path) -> Path:
    """Create ``bots/<bot>/sessions/chat_42/`` and return that path."""
    bot_dir = tmp_path / "bots" / "test_bot"
    session = bot_dir / "sessions" / "chat_42"
    session.mkdir(parents=True)
    return session


@pytest.mark.enable_conversation_search
def test_prepare_skill_config_injects_conversation_search(
    session_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When FTS5 is available, _prepare_skill_config writes the MCP entry."""
    from abyss.claude_runner import _prepare_skill_config

    allowed_tools, _ = _prepare_skill_config(str(session_dir), None)

    assert allowed_tools is not None
    assert "mcp__conversation_search__search_conversations" in allowed_tools

    mcp_json = session_dir / ".mcp.json"
    assert mcp_json.exists()
    config = json.loads(mcp_json.read_text())

    server = config["mcpServers"]["conversation_search"]
    assert server["args"] == ["-m", "abyss.mcp_servers.conversation_search"]
    db_env = server["env"]["ABYSS_CONVERSATION_DB"]
    expected = session_dir.parent.parent / "conversation.db"
    assert Path(db_env) == expected.resolve()


def test_prepare_skill_config_skips_when_fts5_unavailable(
    session_dir: Path,
) -> None:
    """Without the ``enable_conversation_search`` marker the auto-inject is off."""
    from abyss.claude_runner import _prepare_skill_config

    allowed_tools, _ = _prepare_skill_config(str(session_dir), None)
    # Should be None — no skills attached, FTS5 stubbed False, QMD off.
    assert allowed_tools is None
    assert not (session_dir / ".mcp.json").exists()


@pytest.mark.enable_conversation_search
def test_prepare_skill_config_skips_for_invalid_session_path(
    tmp_path: Path,
) -> None:
    """Working directories with no ``bots/<name>/`` ancestor are silently skipped."""
    from abyss.claude_runner import _prepare_skill_config

    shallow = tmp_path / "shallow"
    shallow.mkdir()
    allowed_tools, _ = _prepare_skill_config(str(shallow), None)
    # No ``bots/`` ancestor → MCP injection skipped, no .mcp.json written.
    assert allowed_tools is None
    assert not (shallow / ".mcp.json").exists()


# ─── regression: Codex P2 — bot dir resolution across context types ─────


@pytest.mark.enable_conversation_search
def test_prepare_skill_config_resolves_bot_dir_for_heartbeat(
    tmp_path: Path,
) -> None:
    """Heartbeat working dir is shallower than DM sessions — bot dir
    must still resolve to ``bots/<name>/conversation.db``, not
    ``bots/conversation.db``. Regression for PR #7 review.
    """
    import sys

    from abyss.claude_runner import _prepare_skill_config

    bot_path = tmp_path / "bots" / "alpha"
    heartbeat_dir = bot_path / "heartbeat_sessions"
    heartbeat_dir.mkdir(parents=True)

    allowed_tools, _ = _prepare_skill_config(str(heartbeat_dir), None)

    assert allowed_tools is not None
    config = json.loads((heartbeat_dir / ".mcp.json").read_text())
    server = config["mcpServers"]["conversation_search"]
    assert server["command"] == sys.executable
    db_env = Path(server["env"]["ABYSS_CONVERSATION_DB"]).resolve()
    expected_db = (bot_path / "conversation.db").resolve()
    assert db_env == expected_db


@pytest.mark.enable_conversation_search
def test_prepare_skill_config_resolves_bot_dir_for_cron(
    tmp_path: Path,
) -> None:
    """Cron sessions sit at ``bots/<name>/cron_sessions/<job>/`` —
    DB path must still target the bot's own directory."""
    from abyss.claude_runner import _prepare_skill_config

    bot_path = tmp_path / "bots" / "alpha"
    cron_dir = bot_path / "cron_sessions" / "morning_report"
    cron_dir.mkdir(parents=True)

    allowed_tools, _ = _prepare_skill_config(str(cron_dir), None)

    assert allowed_tools is not None
    config = json.loads((cron_dir / ".mcp.json").read_text())
    server = config["mcpServers"]["conversation_search"]
    db_env = Path(server["env"]["ABYSS_CONVERSATION_DB"]).resolve()
    expected_db = (bot_path / "conversation.db").resolve()
    assert db_env == expected_db
