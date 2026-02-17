"""Tests for cclaw.handlers module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cclaw.handlers import _is_user_allowed, make_handlers
from cclaw.utils import split_message

MOCK_CANCEL = "cclaw.handlers.cancel_process"
MOCK_IS_RUNNING = "cclaw.handlers.is_process_running"


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
    assert len(handlers) == 14


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
    message_handler = handlers[13]

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
async def test_cancel_handler_no_process(bot_path, bot_config, mock_update):
    """Cancel handler replies when no process is running."""
    handlers = make_handlers("test-bot", bot_path, bot_config)
    cancel_handler = handlers[9]

    with patch(MOCK_IS_RUNNING, return_value=False):
        await cancel_handler.callback(mock_update, MagicMock())

    call_text = mock_update.message.reply_text.call_args[0][0]
    assert "No running process" in call_text


@pytest.mark.asyncio
async def test_cancel_handler_kills_process(bot_path, bot_config, mock_update):
    """Cancel handler kills running process."""
    handlers = make_handlers("test-bot", bot_path, bot_config)
    cancel_handler = handlers[9]

    with patch(MOCK_IS_RUNNING, return_value=True), patch(MOCK_CANCEL, return_value=True):
        await cancel_handler.callback(mock_update, MagicMock())

    call_text = mock_update.message.reply_text.call_args[0][0]
    assert "cancelled" in call_text.lower() or "\u26d4" in call_text


@pytest.mark.asyncio
async def test_send_handler_no_args(bot_path, bot_config, mock_update):
    """Send handler shows usage when no filename provided."""
    handlers = make_handlers("test-bot", bot_path, bot_config)
    send_handler = handlers[5]

    mock_context = MagicMock()
    mock_context.args = []
    await send_handler.callback(mock_update, mock_context)

    call_text = mock_update.message.reply_text.call_args[0][0]
    assert "Usage" in call_text or "No files" in call_text


@pytest.mark.asyncio
async def test_send_handler_file_not_found(bot_path, bot_config, mock_update):
    """Send handler replies when file not found."""
    handlers = make_handlers("test-bot", bot_path, bot_config)
    send_handler = handlers[5]

    mock_context = MagicMock()
    mock_context.args = ["nonexistent.txt"]
    await send_handler.callback(mock_update, mock_context)

    call_text = mock_update.message.reply_text.call_args[0][0]
    assert "not found" in call_text.lower()


@pytest.mark.asyncio
async def test_send_handler_sends_file(bot_path, bot_config, mock_update):
    """Send handler sends an existing workspace file."""
    handlers = make_handlers("test-bot", bot_path, bot_config)
    send_handler = handlers[5]

    # Create a session with a file in workspace
    session_dir = bot_path / "sessions" / "chat_67890"
    session_dir.mkdir(parents=True, exist_ok=True)
    workspace = session_dir / "workspace"
    workspace.mkdir(exist_ok=True)
    test_file = workspace / "test.txt"
    test_file.write_text("hello")

    mock_context = MagicMock()
    mock_context.args = ["test.txt"]
    mock_update.message.reply_document = AsyncMock()

    await send_handler.callback(mock_update, mock_context)

    mock_update.message.reply_document.assert_called_once()


@pytest.mark.asyncio
async def test_model_handler_show_current(bot_path, bot_config, mock_update):
    """Model handler shows current model when no args."""
    handlers = make_handlers("test-bot", bot_path, bot_config)
    model_handler = handlers[7]

    mock_context = MagicMock()
    mock_context.args = []
    await model_handler.callback(mock_update, mock_context)

    call_text = mock_update.message.reply_text.call_args[0][0]
    assert "sonnet" in call_text


@pytest.mark.asyncio
async def test_model_handler_change_model(bot_path, bot_config, mock_update):
    """Model handler changes model and saves to bot.yaml."""
    handlers = make_handlers("test-bot", bot_path, bot_config)
    model_handler = handlers[7]

    mock_context = MagicMock()
    mock_context.args = ["opus"]

    with patch("cclaw.handlers.save_bot_config") as mock_save:
        await model_handler.callback(mock_update, mock_context)
        mock_save.assert_called_once()
        saved_config = mock_save.call_args[0][1]
        assert saved_config["model"] == "opus"

    call_text = mock_update.message.reply_text.call_args[0][0]
    assert "opus" in call_text


@pytest.mark.asyncio
async def test_model_handler_invalid_model(bot_path, bot_config, mock_update):
    """Model handler rejects invalid model names."""
    handlers = make_handlers("test-bot", bot_path, bot_config)
    model_handler = handlers[7]

    mock_context = MagicMock()
    mock_context.args = ["gpt4"]
    await model_handler.callback(mock_update, mock_context)

    call_text = mock_update.message.reply_text.call_args[0][0]
    assert "Invalid" in call_text


@pytest.mark.asyncio
async def test_message_handler_passes_model(bot_path, bot_config, mock_update):
    """Message handler passes model to run_claude."""
    bot_config["model"] = "opus"
    handlers = make_handlers("test-bot", bot_path, bot_config)
    message_handler = handlers[13]

    with patch("cclaw.handlers.run_claude", new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = "response"
        await message_handler.callback(mock_update, MagicMock())

    call_kwargs = mock_claude.call_args[1]
    assert call_kwargs["model"] == "opus"


@pytest.mark.asyncio
async def test_files_handler_empty(bot_path, bot_config, mock_update):
    """Files handler shows empty message when no files."""
    handlers = make_handlers("test-bot", bot_path, bot_config)
    files_handler = handlers[4]

    await files_handler.callback(mock_update, MagicMock())

    call_text = mock_update.message.reply_text.call_args[0][0]
    assert "No files" in call_text


@pytest.mark.asyncio
async def test_skills_handler_empty(bot_path, bot_config, mock_update):
    """Skills handler shows empty message when no skills exist."""
    handlers = make_handlers("test-bot", bot_path, bot_config)
    skills_handler = handlers[10]

    with patch("cclaw.skill.list_skills", return_value=[]):
        await skills_handler.callback(mock_update, MagicMock())

    call_text = mock_update.message.reply_text.call_args[0][0]
    assert "No skills available" in call_text


@pytest.mark.asyncio
async def test_skills_handler_lists_all(bot_path, bot_config, mock_update):
    """Skills handler lists all skills including unattached ones."""
    handlers = make_handlers("test-bot", bot_path, bot_config)
    skills_handler = handlers[10]

    mock_skills = [
        {"name": "attached-skill", "type": "cli", "status": "active", "description": "A tool"},
        {"name": "unattached-skill", "type": None, "status": "active", "description": "Markdown"},
    ]

    with (
        patch("cclaw.skill.list_skills", return_value=mock_skills),
        patch("cclaw.skill.bots_using_skill", side_effect=[["test-bot"], []]),
    ):
        await skills_handler.callback(mock_update, MagicMock())

    call_text = mock_update.message.reply_text.call_args[0][0]
    assert "attached-skill" in call_text
    assert "unattached-skill" in call_text
    assert "All Skills" in call_text


@pytest.mark.asyncio
async def test_skill_handler_no_args(bot_path, bot_config, mock_update):
    """Skill handler shows usage when no args."""
    handlers = make_handlers("test-bot", bot_path, bot_config)
    skill_handler = handlers[11]

    mock_context = MagicMock()
    mock_context.args = []
    await skill_handler.callback(mock_update, mock_context)

    call_text = mock_update.message.reply_text.call_args[0][0]
    assert "Skill Commands" in call_text


@pytest.mark.asyncio
async def test_skill_handler_list_empty(bot_path, bot_config, mock_update):
    """Skill handler list shows empty when no skills attached."""
    handlers = make_handlers("test-bot", bot_path, bot_config)
    skill_handler = handlers[11]

    mock_context = MagicMock()
    mock_context.args = ["list"]
    await skill_handler.callback(mock_update, mock_context)

    call_text = mock_update.message.reply_text.call_args[0][0]
    assert "No skills attached" in call_text


@pytest.mark.asyncio
async def test_skill_handler_attach(bot_path, bot_config, mock_update):
    """Skill handler attach adds a skill."""
    handlers = make_handlers("test-bot", bot_path, bot_config)
    skill_handler = handlers[11]

    mock_context = MagicMock()
    mock_context.args = ["attach", "test-skill"]

    with (
        patch("cclaw.skill.is_skill", return_value=True),
        patch("cclaw.skill.skill_status", return_value="active"),
        patch("cclaw.skill.attach_skill_to_bot") as mock_attach,
    ):
        bot_config["skills"] = ["test-skill"]
        await skill_handler.callback(mock_update, mock_context)
        mock_attach.assert_called_once_with("test-bot", "test-skill")

    call_text = mock_update.message.reply_text.call_args[0][0]
    assert "attached" in call_text


@pytest.mark.asyncio
async def test_skill_handler_attach_not_found(bot_path, bot_config, mock_update):
    """Skill handler attach rejects nonexistent skill."""
    handlers = make_handlers("test-bot", bot_path, bot_config)
    skill_handler = handlers[11]

    mock_context = MagicMock()
    mock_context.args = ["attach", "nonexistent"]

    with patch("cclaw.skill.is_skill", return_value=False):
        await skill_handler.callback(mock_update, mock_context)

    call_text = mock_update.message.reply_text.call_args[0][0]
    assert "not found" in call_text


@pytest.mark.asyncio
async def test_skill_handler_detach(bot_path, bot_config, mock_update):
    """Skill handler detach removes a skill."""
    bot_config["skills"] = ["test-skill"]
    handlers = make_handlers("test-bot", bot_path, bot_config)
    skill_handler = handlers[11]

    mock_context = MagicMock()
    mock_context.args = ["detach", "test-skill"]

    with patch("cclaw.skill.detach_skill_from_bot") as mock_detach:
        bot_config["skills"] = []
        await skill_handler.callback(mock_update, mock_context)
        mock_detach.assert_called_once_with("test-bot", "test-skill")

    call_text = mock_update.message.reply_text.call_args[0][0]
    assert "detached" in call_text


@pytest.mark.asyncio
async def test_message_handler_passes_skill_names(bot_path, bot_config, mock_update):
    """Message handler passes skill_names to run_claude when skills are attached."""
    bot_config["skills"] = ["my-skill"]
    handlers = make_handlers("test-bot", bot_path, bot_config)
    message_handler = handlers[13]

    with patch("cclaw.handlers.run_claude", new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = "response"
        await message_handler.callback(mock_update, MagicMock())

    call_kwargs = mock_claude.call_args[1]
    assert call_kwargs["skill_names"] == ["my-skill"]


@pytest.mark.asyncio
async def test_message_handler_no_skill_names(bot_path, bot_config, mock_update):
    """Message handler passes None for skill_names when no skills attached."""
    handlers = make_handlers("test-bot", bot_path, bot_config)
    message_handler = handlers[13]

    with patch("cclaw.handlers.run_claude", new_callable=AsyncMock) as mock_claude:
        mock_claude.return_value = "response"
        await message_handler.callback(mock_update, MagicMock())

    call_kwargs = mock_claude.call_args[1]
    assert call_kwargs["skill_names"] is None
