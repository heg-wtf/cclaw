"""Session directory management for cclaw."""

from __future__ import annotations

import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

CLAUDE_SESSION_ID_FILE = ".claude_session_id"
MEMORY_FILE_NAME = "MEMORY.md"
MAX_CONVERSATION_HISTORY_TURNS = 20


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
    clear_claude_session_id(directory)


def reset_all_session(bot_path: Path, chat_id: int) -> None:
    """Reset a session completely by deleting the entire session directory."""
    directory = session_directory(bot_path, chat_id)
    if directory.exists():
        shutil.rmtree(directory)


def get_claude_session_id(session_directory: Path) -> str | None:
    """Read stored Claude Code session ID."""
    path = session_directory / CLAUDE_SESSION_ID_FILE
    if path.exists():
        return path.read_text().strip()
    return None


def save_claude_session_id(session_directory: Path, session_id: str) -> None:
    """Store Claude Code session ID."""
    (session_directory / CLAUDE_SESSION_ID_FILE).write_text(session_id)


def clear_claude_session_id(session_directory: Path) -> None:
    """Remove stored Claude Code session ID."""
    (session_directory / CLAUDE_SESSION_ID_FILE).unlink(missing_ok=True)


def load_conversation_history(
    session_directory: Path, max_turns: int = MAX_CONVERSATION_HISTORY_TURNS
) -> str | None:
    """Read last N turns from conversation.md.

    conversation.md format: "## role (timestamp)\\n\\ncontent\\n" repeated.
    Parses sections starting with "## user" or "## assistant" and returns
    the most recent max_turns entries.

    Returns None if conversation.md doesn't exist or is empty.
    """
    conversation_file = session_directory / "conversation.md"
    if not conversation_file.exists():
        return None

    content = conversation_file.read_text()
    if not content.strip():
        return None

    # Split into sections by "## user" or "## assistant" headers
    sections = re.split(r"(?=\n## (?:user|assistant) \()", content)
    # Filter out empty sections
    sections = [s.strip() for s in sections if s.strip()]

    if not sections:
        return None

    # Take the last max_turns sections
    recent_sections = sections[-max_turns:]
    return "\n\n".join(recent_sections)


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


# --- Bot-level memory ---


def memory_file_path(bot_path: Path) -> Path:
    """Return the path to the bot's MEMORY.md file."""
    return bot_path / MEMORY_FILE_NAME


def load_bot_memory(bot_path: Path) -> str | None:
    """Load the bot's MEMORY.md content.

    Returns None if MEMORY.md doesn't exist or is empty.
    """
    path = memory_file_path(bot_path)
    if not path.exists():
        return None
    content = path.read_text()
    if not content.strip():
        return None
    return content


def save_bot_memory(bot_path: Path, content: str) -> None:
    """Save content to the bot's MEMORY.md file."""
    memory_file_path(bot_path).write_text(content)


def clear_bot_memory(bot_path: Path) -> None:
    """Delete the bot's MEMORY.md file."""
    memory_file_path(bot_path).unlink(missing_ok=True)
