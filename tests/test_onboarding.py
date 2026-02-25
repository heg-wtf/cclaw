"""Tests for cclaw.onboarding module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cclaw.onboarding import (
    EnvironmentCheckResult,
    _is_daemon_running,
    check_claude_code,
    check_node,
    check_python,
    create_bot,
    run_environment_checks,
    validate_telegram_token,
)


def test_check_python():
    """check_python should always succeed."""
    result = check_python()
    assert result.available is True
    assert result.name == "Python"
    assert result.version


def test_check_node_installed():
    """check_node returns available=True when node is found."""
    with patch("cclaw.onboarding.shutil.which", return_value="/usr/local/bin/node"):
        with patch("cclaw.onboarding.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="v20.11.0\n", stderr="")
            result = check_node()
            assert result.available is True
            assert "20" in result.version


def test_check_node_missing():
    """check_node returns available=False when node is not found."""
    with patch("cclaw.onboarding.shutil.which", return_value=None):
        result = check_node()
        assert result.available is False


def test_check_claude_code_installed():
    """check_claude_code returns available=True when claude is found."""
    with patch("cclaw.onboarding.shutil.which", return_value="/usr/local/bin/claude"):
        with patch("cclaw.onboarding.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="1.0.23\n", stderr="")
            result = check_claude_code()
            assert result.available is True
            assert "1.0.23" in result.version


def test_check_claude_code_missing():
    """check_claude_code returns available=False when claude is not found."""
    with patch("cclaw.onboarding.shutil.which", return_value=None):
        result = check_claude_code()
        assert result.available is False
        assert "npm install" in result.message


def test_run_environment_checks():
    """run_environment_checks returns a list of 3 checks."""
    with patch("cclaw.onboarding.shutil.which", return_value="/usr/bin/fake"):
        with patch("cclaw.onboarding.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="v1.0.0\n", stderr="")
            checks = run_environment_checks()
            assert len(checks) == 3
            assert all(isinstance(c, EnvironmentCheckResult) for c in checks)


@pytest.mark.asyncio
async def test_validate_telegram_token_valid():
    """validate_telegram_token returns bot info for valid token."""
    mock_bot_info = MagicMock()
    mock_bot_info.username = "test_bot"
    mock_bot_info.first_name = "Test Bot"

    with patch("telegram.Bot") as mock_bot_class:
        mock_bot = MagicMock()
        mock_bot.get_me = AsyncMock(return_value=mock_bot_info)
        mock_bot_class.return_value = mock_bot

        result = await validate_telegram_token("valid-token")
        assert result is not None
        assert result["username"] == "@test_bot"
        assert result["botname"] == "Test Bot"


@pytest.mark.asyncio
async def test_validate_telegram_token_invalid():
    """validate_telegram_token returns None for invalid token."""
    with patch("telegram.Bot") as mock_bot_class:
        mock_bot = MagicMock()
        mock_bot.get_me = AsyncMock(side_effect=Exception("Invalid token"))
        mock_bot_class.return_value = mock_bot

        result = await validate_telegram_token("invalid-token")
        assert result is None


def test_create_bot(tmp_path, monkeypatch):
    """create_bot creates all necessary files."""
    monkeypatch.setenv("CCLAW_HOME", str(tmp_path / ".cclaw"))

    token = "123456:ABCDEF"
    bot_info = {"username": "@test_bot", "botname": "Test Bot"}
    profile = {
        "name": "test-bot",
        "personality": "Helpful assistant",
        "description": "General help",
    }

    create_bot(token, bot_info, profile)

    bot_directory = tmp_path / ".cclaw" / "bots" / "test-bot"
    assert (bot_directory / "bot.yaml").exists()
    assert (bot_directory / "CLAUDE.md").exists()
    assert (bot_directory / "sessions").exists()

    config_path = tmp_path / ".cclaw" / "config.yaml"
    assert config_path.exists()


def test_create_bot_restarts_daemon_when_running(tmp_path, monkeypatch):
    """create_bot restarts daemon automatically when daemon is running."""
    monkeypatch.setenv("CCLAW_HOME", str(tmp_path / ".cclaw"))

    token = "123456:ABCDEF"
    bot_info = {"username": "@new_bot", "botname": "New Bot"}
    profile = {
        "name": "new-bot",
        "personality": "Helpful",
        "description": "Test",
    }

    with patch("cclaw.onboarding._is_daemon_running", return_value=True):
        with patch("cclaw.onboarding._restart_daemon") as mock_restart:
            create_bot(token, bot_info, profile)
            mock_restart.assert_called_once()


def test_create_bot_no_restart_when_daemon_not_running(tmp_path, monkeypatch):
    """create_bot does not restart when daemon is not running."""
    monkeypatch.setenv("CCLAW_HOME", str(tmp_path / ".cclaw"))

    token = "123456:ABCDEF"
    bot_info = {"username": "@new_bot", "botname": "New Bot"}
    profile = {
        "name": "new-bot",
        "personality": "Helpful",
        "description": "Test",
    }

    with patch("cclaw.onboarding._is_daemon_running", return_value=False):
        with patch("cclaw.onboarding._restart_daemon") as mock_restart:
            create_bot(token, bot_info, profile)
            mock_restart.assert_not_called()


def test_is_daemon_running_with_plist(tmp_path):
    """_is_daemon_running returns True when plist exists."""
    plist_path = tmp_path / "com.cclaw.daemon.plist"
    plist_path.write_text("<plist/>")

    with patch("cclaw.bot_manager._plist_path", return_value=plist_path):
        assert _is_daemon_running() is True


def test_is_daemon_running_without_plist(tmp_path):
    """_is_daemon_running returns False when plist does not exist."""
    plist_path = tmp_path / "com.cclaw.daemon.plist"

    with patch("cclaw.bot_manager._plist_path", return_value=plist_path):
        assert _is_daemon_running() is False
