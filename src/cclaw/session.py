"""Session directory management for cclaw."""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path


def session_directory(bot_path: Path, chat_id: int) -> Path:
    """Return the session directory path for a given chat."""
    return bot_path / "sessions" / f"chat_{chat_id}"


def ensure_session(bot_path: Path, chat_id: int) -> Path:
    """Ensure a session directory exists with required files.

    Creates the session directory, copies the bot's CLAUDE.md into it,
    and creates the workspace subdirectory.

    Returns the session directory path.
    """
    directory = session_directory(bot_path, chat_id)
    directory.mkdir(parents=True, exist_ok=True)

    workspace = directory / "workspace"
    workspace.mkdir(exist_ok=True)

    session_claude_md = directory / "CLAUDE.md"
    bot_claude_md = bot_path / "CLAUDE.md"

    if not session_claude_md.exists() and bot_claude_md.exists():
        shutil.copy2(bot_claude_md, session_claude_md)

    return directory


def reset_session(bot_path: Path, chat_id: int) -> None:
    """Reset a session by deleting conversation.md (keep workspace)."""
    directory = session_directory(bot_path, chat_id)
    conversation_file = directory / "conversation.md"
    if conversation_file.exists():
        conversation_file.unlink()


def reset_all_session(bot_path: Path, chat_id: int) -> None:
    """Reset a session completely by deleting the entire session directory."""
    directory = session_directory(bot_path, chat_id)
    if directory.exists():
        shutil.rmtree(directory)


def log_conversation(session_directory: Path, role: str, content: str) -> None:
    """Append a conversation entry to conversation.md.

    Args:
        session_directory: Path to the session directory.
        role: Either 'user' or 'assistant'.
        content: The message content.
    """
    conversation_file = session_directory / "conversation.md"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    entry = f"\n## {role} ({timestamp})\n\n{content}\n"

    with open(conversation_file, "a") as file:
        file.write(entry)


def list_workspace_files(session_directory: Path) -> list[str]:
    """List all files in the session's workspace directory.

    Returns a list of relative file paths within the workspace.
    """
    workspace = session_directory / "workspace"
    if not workspace.exists():
        return []

    files = []
    for file_path in sorted(workspace.rglob("*")):
        if file_path.is_file():
            files.append(str(file_path.relative_to(workspace)))
    return files
