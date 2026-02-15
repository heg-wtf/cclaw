"""Tests for cclaw.session module."""

from pathlib import Path

import pytest

from cclaw.session import (
    ensure_session,
    list_workspace_files,
    log_conversation,
    reset_all_session,
    reset_session,
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
