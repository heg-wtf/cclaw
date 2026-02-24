"""Tests for cclaw.session module."""

import pytest

from cclaw.session import (
    clear_bot_memory,
    clear_claude_session_id,
    collect_session_chat_ids,
    ensure_session,
    get_claude_session_id,
    list_workspace_files,
    load_bot_memory,
    load_conversation_history,
    log_conversation,
    memory_file_path,
    reset_all_session,
    reset_session,
    save_bot_memory,
    save_claude_session_id,
    session_directory,
)


@pytest.fixture
def bot_path(tmp_path):
    """Create a fake bot directory with CLAUDE.md."""
    bot_directory = tmp_path / "bots" / "test-bot"
    bot_directory.mkdir(parents=True)
    (bot_directory / "CLAUDE.md").write_text("# test-bot\n\nBot instructions.")
    (bot_directory / "sessions").mkdir()
    return bot_directory


def test_session_directory(bot_path):
    """session_directory returns expected path."""
    result = session_directory(bot_path, 12345)
    assert result == bot_path / "sessions" / "chat_12345"


def test_ensure_session_creates_directory(bot_path):
    """ensure_session creates session dir, workspace, and copies CLAUDE.md."""
    directory = ensure_session(bot_path, 12345)

    assert directory.exists()
    assert (directory / "workspace").exists()
    assert (directory / "CLAUDE.md").exists()
    assert (directory / "CLAUDE.md").read_text() == "# test-bot\n\nBot instructions."


def test_ensure_session_idempotent(bot_path):
    """ensure_session can be called multiple times without error."""
    directory1 = ensure_session(bot_path, 12345)
    (directory1 / "CLAUDE.md").write_text("modified content")

    directory2 = ensure_session(bot_path, 12345)
    assert directory1 == directory2
    assert (directory2 / "CLAUDE.md").read_text() == "modified content"


def test_reset_session(bot_path):
    """reset_session deletes conversation.md but keeps workspace."""
    directory = ensure_session(bot_path, 12345)

    conversation_file = directory / "conversation.md"
    conversation_file.write_text("some conversation")

    workspace_file = directory / "workspace" / "test.txt"
    workspace_file.write_text("workspace content")

    reset_session(bot_path, 12345)

    assert not conversation_file.exists()
    assert workspace_file.exists()
    assert (directory / "CLAUDE.md").exists()


def test_reset_session_no_conversation(bot_path):
    """reset_session doesn't error if conversation.md doesn't exist."""
    ensure_session(bot_path, 12345)
    reset_session(bot_path, 12345)


def test_reset_all_session(bot_path):
    """reset_all_session deletes the entire session directory."""
    directory = ensure_session(bot_path, 12345)
    (directory / "workspace" / "test.txt").write_text("data")
    (directory / "conversation.md").write_text("chat")

    reset_all_session(bot_path, 12345)

    assert not directory.exists()


def test_reset_all_session_nonexistent(bot_path):
    """reset_all_session doesn't error if session doesn't exist."""
    reset_all_session(bot_path, 99999)


def test_log_conversation(bot_path):
    """log_conversation appends entries to conversation.md."""
    directory = ensure_session(bot_path, 12345)

    log_conversation(directory, "user", "Hello")
    log_conversation(directory, "assistant", "Hi there!")

    content = (directory / "conversation.md").read_text()
    assert "## user" in content
    assert "Hello" in content
    assert "## assistant" in content
    assert "Hi there!" in content


def test_list_workspace_files(bot_path):
    """list_workspace_files returns files in workspace."""
    directory = ensure_session(bot_path, 12345)
    workspace = directory / "workspace"

    (workspace / "file1.txt").write_text("content1")
    (workspace / "file2.py").write_text("content2")

    sub_directory = workspace / "subdir"
    sub_directory.mkdir()
    (sub_directory / "file3.md").write_text("content3")

    files = list_workspace_files(directory)
    assert len(files) == 3
    assert "file1.txt" in files
    assert "file2.py" in files
    assert "subdir/file3.md" in files


def test_list_workspace_files_empty(bot_path):
    """list_workspace_files returns empty list for empty workspace."""
    directory = ensure_session(bot_path, 12345)
    files = list_workspace_files(directory)
    assert files == []


def test_list_workspace_files_no_workspace(tmp_path):
    """list_workspace_files returns empty list if workspace doesn't exist."""
    files = list_workspace_files(tmp_path / "nonexistent")
    assert files == []


# --- Claude session ID tests ---


def test_get_claude_session_id_none(tmp_path):
    """get_claude_session_id returns None when file doesn't exist."""
    assert get_claude_session_id(tmp_path) is None


def test_save_and_get_claude_session_id(tmp_path):
    """save_claude_session_id and get_claude_session_id round-trip."""
    save_claude_session_id(tmp_path, "abc-123-def")
    assert get_claude_session_id(tmp_path) == "abc-123-def"


def test_clear_claude_session_id(tmp_path):
    """clear_claude_session_id removes the session ID file."""
    save_claude_session_id(tmp_path, "abc-123")
    clear_claude_session_id(tmp_path)
    assert get_claude_session_id(tmp_path) is None


def test_clear_claude_session_id_missing(tmp_path):
    """clear_claude_session_id doesn't error when file is missing."""
    clear_claude_session_id(tmp_path)  # should not raise


# --- Conversation history tests ---


def test_load_conversation_history_empty(tmp_path):
    """load_conversation_history returns None when conversation.md doesn't exist."""
    assert load_conversation_history(tmp_path) is None


def test_load_conversation_history_empty_file(tmp_path):
    """load_conversation_history returns None when conversation.md is empty."""
    (tmp_path / "conversation.md").write_text("")
    assert load_conversation_history(tmp_path) is None


def test_load_conversation_history_full(bot_path):
    """load_conversation_history returns all turns when under max_turns."""
    directory = ensure_session(bot_path, 12345)
    log_conversation(directory, "user", "Hello")
    log_conversation(directory, "assistant", "Hi there!")
    log_conversation(directory, "user", "How are you?")
    log_conversation(directory, "assistant", "I'm good!")

    history = load_conversation_history(directory)
    assert history is not None
    assert "Hello" in history
    assert "Hi there!" in history
    assert "How are you?" in history
    assert "I'm good!" in history


def test_load_conversation_history_truncates(bot_path):
    """load_conversation_history returns only last max_turns entries."""
    directory = ensure_session(bot_path, 12345)

    # Write 25 turns (more than default 20)
    for i in range(25):
        role = "user" if i % 2 == 0 else "assistant"
        log_conversation(directory, role, f"Message {i}")

    history = load_conversation_history(directory, max_turns=20)
    assert history is not None
    # First 5 messages should be truncated
    assert "Message 0" not in history
    assert "Message 4" not in history
    # Last 20 should be present
    assert "Message 5" in history
    assert "Message 24" in history


# --- Reset clears session ID tests ---


def test_reset_session_clears_session_id(bot_path):
    """reset_session also clears the stored Claude session ID."""
    directory = ensure_session(bot_path, 12345)
    save_claude_session_id(directory, "test-session-id")
    (directory / "conversation.md").write_text("some conversation")

    reset_session(bot_path, 12345)

    assert get_claude_session_id(directory) is None


def test_reset_all_session_clears_session_id(bot_path):
    """reset_all_session removes the entire directory including session ID."""
    directory = ensure_session(bot_path, 12345)
    save_claude_session_id(directory, "test-session-id")

    reset_all_session(bot_path, 12345)

    # Directory is gone, so session ID is gone too
    assert not directory.exists()
    assert get_claude_session_id(directory) is None


# --- Bot memory tests ---


def test_memory_file_path(bot_path):
    """memory_file_path returns expected path."""
    result = memory_file_path(bot_path)
    assert result == bot_path / "MEMORY.md"


def test_load_bot_memory_none(bot_path):
    """load_bot_memory returns None when MEMORY.md doesn't exist."""
    assert load_bot_memory(bot_path) is None


def test_load_bot_memory_empty(bot_path):
    """load_bot_memory returns None when MEMORY.md is empty."""
    (bot_path / "MEMORY.md").write_text("")
    assert load_bot_memory(bot_path) is None


def test_load_bot_memory_whitespace_only(bot_path):
    """load_bot_memory returns None when MEMORY.md is whitespace only."""
    (bot_path / "MEMORY.md").write_text("   \n\n  ")
    assert load_bot_memory(bot_path) is None


def test_save_and_load_bot_memory(bot_path):
    """save_bot_memory and load_bot_memory round-trip."""
    save_bot_memory(bot_path, "# Memory\n\n- User likes Python")
    content = load_bot_memory(bot_path)
    assert content == "# Memory\n\n- User likes Python"


def test_clear_bot_memory(bot_path):
    """clear_bot_memory removes the MEMORY.md file."""
    save_bot_memory(bot_path, "some memory")
    clear_bot_memory(bot_path)
    assert load_bot_memory(bot_path) is None
    assert not (bot_path / "MEMORY.md").exists()


def test_clear_bot_memory_missing(bot_path):
    """clear_bot_memory doesn't error when file is missing."""
    clear_bot_memory(bot_path)  # should not raise


# --- collect_session_chat_ids tests ---


def test_collect_session_chat_ids(bot_path):
    """collect_session_chat_ids returns chat IDs from session directories."""
    ensure_session(bot_path, 111)
    ensure_session(bot_path, 222)
    ensure_session(bot_path, 333)

    chat_ids = collect_session_chat_ids(bot_path)
    assert chat_ids == [111, 222, 333]


def test_collect_session_chat_ids_empty(bot_path):
    """collect_session_chat_ids returns empty list when no sessions exist."""
    chat_ids = collect_session_chat_ids(bot_path)
    assert chat_ids == []


def test_collect_session_chat_ids_no_sessions_directory(tmp_path):
    """collect_session_chat_ids returns empty list when sessions dir doesn't exist."""
    chat_ids = collect_session_chat_ids(tmp_path / "nonexistent")
    assert chat_ids == []


def test_collect_session_chat_ids_ignores_non_chat_directories(bot_path):
    """collect_session_chat_ids ignores directories that don't match chat_<id> pattern."""
    ensure_session(bot_path, 111)
    (bot_path / "sessions" / "not_a_chat").mkdir()
    (bot_path / "sessions" / "chat_abc").mkdir()  # non-numeric

    chat_ids = collect_session_chat_ids(bot_path)
    assert chat_ids == [111]
