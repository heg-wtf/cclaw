"""Tests for cclaw.handlers module."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cclaw.handlers import _is_user_allowed, make_handlers
from cclaw.utils import split_message


@pytest.fixture
def bot_path(tmp_path):
    """Create a bot directory."""
    bot_directory = tmp_path / "bots" / "test-bot"
    bot_directory.mkdir(parents=True)
    (bot_directory / "CLAUDE.md").write_text("# test-bot")
    (bot_directory / "sessions").mkdir()
    return bot_directory


@pytest.fixture
def bot_config():
    """Return a test bot config."""
    return {
        "telegram_token": "fake-token",
        "telegram_username": "@test_bot",
        "telegram_botname": "Test Bot",
        "personality": "Helpful assistant",
        "description": "General help",
        "allowed_users": [],
        "claude_args": [],
        "command_timeout": 30,
    }


def test_make_handlers_returns_handlers(bot_path, bot_config):
    """make_handlers returns a list of handlers."""
    handlers = make_handlers("test-bot", bot_path, bot_config)
    assert len(handlers) == 9


def test_is_user_allowed_empty_list():
    """Empty allowed_users means all users allowed."""
    assert _is_user_allowed(12345, [])


def test_is_user_allowed_in_list():
    """User in allowed list is allowed."""
    assert _is_user_allowed(12345, [12345, 67890])


def test_is_user_allowed_not_in_list():
    """User not in allowed list is denied."""
    assert not _is_user_allowed(12345, [67890])


def test_split_message_short():
    """Short messages are not split."""
    chunks = split_message("Hello world")
    assert len(chunks) == 1
    assert chunks[0] == "Hello world"


def test_split_message_long():
    """Long messages are split at newlines."""
    text = "\n".join(f"Line {i}" for i in range(1000))
    chunks = split_message(text, limit=100)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 100


def test_split_message_no_newlines():
    """Messages without newlines are split at limit."""
    text = "x" * 200
    chunks = split_message(text, limit=100)
    assert len(chunks) == 2
    assert chunks[0] == "x" * 100
    assert chunks[1] == "x" * 100


def test_split_message_exact_limit():
    """Message exactly at limit is not split."""
    text = "x" * 4096
    chunks = split_message(text)
    assert len(chunks) == 1


@pytest.fixture
def mock_update():
    """Create a mock Telegram Update."""
    update = MagicMock()
    update.effective_user.id = 12345
    update.effective_chat.id = 67890
    update.message.text = "Hello Claude"
    update.message.reply_text = AsyncMock()
    update.message.chat.send_action = AsyncMock()
    return update


@pytest.mark.asyncio
async def test_start_handler(bot_path, bot_config, mock_update):
    """Start handler sends bot introduction."""
    handlers = make_handlers("test-bot", bot_path, bot_config)
    start_handler = handlers[0]

    await start_handler.callback(mock_update, MagicMock())

    mock_update.message.reply_text.assert_called_once()
    call_text = mock_update.message.reply_text.call_args[0][0]
    assert "test-bot" in call_text


@pytest.mark.asyncio
async def test_help_handler(bot_path, bot_config, mock_update):
    """Help handler sends command list."""
    handlers = make_handlers("test-bot", bot_path, bot_config)
    help_handler = handlers[1]

    await help_handler.callback(mock_update, MagicMock())

    call_text = mock_update.message.reply_text.call_args[0][0]
    assert "/start" in call_text
    assert "/reset" in call_text


@pytest.mark.asyncio
async def test_reset_handler(bot_path, bot_config, mock_update):
    """Reset handler calls reset_session."""
    handlers = make_handlers("test-bot", bot_path, bot_config)
    reset_handler = handlers[2]

    with patch("cclaw.handlers.reset_session") as mock_reset:
        await reset_handler.callback(mock_update, MagicMock())
        mock_reset.assert_called_once_with(bot_path, 67890)


@pytest.mark.asyncio
async def test_message_handler_calls_claude(bot_path, bot_config, mock_update):
    """Message handler forwards to Claude and replies."""
    handlers = make_handlers("test-bot", bot_path, bot_config)
    message_handler = handlers[8]

    with patch("cclaw.handlers.run_claude", new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = "Claude response"
        await message_handler.callback(mock_update, MagicMock())

    mock_update.message.reply_text.assert_called()
    reply_text = mock_update.message.reply_text.call_args[0][0]
    assert "Claude response" in reply_text


@pytest.mark.asyncio
async def test_message_handler_unauthorized(bot_path, bot_config, mock_update):
    """Message handler rejects unauthorized users."""
    bot_config["allowed_users"] = [99999]
    handlers = make_handlers("test-bot", bot_path, bot_config)
    message_handler = handlers[6]

    await message_handler.callback(mock_update, MagicMock())

    mock_update.message.reply_text.assert_called_with("Unauthorized.")


@pytest.mark.asyncio
async def test_files_handler_empty(bot_path, bot_config, mock_update):
    """Files handler shows empty message when no files."""
    handlers = make_handlers("test-bot", bot_path, bot_config)
    files_handler = handlers[4]

    await files_handler.callback(mock_update, MagicMock())

    call_text = mock_update.message.reply_text.call_args[0][0]
    assert "No files" in call_text
