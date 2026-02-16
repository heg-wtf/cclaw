"""Claude Code subprocess runner."""

from __future__ import annotations

import asyncio
import logging
import shutil

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 300

# Tracks running processes per session key (e.g. "botname:chat_id")
_running_processes: dict[str, asyncio.subprocess.Process] = {}


def register_process(session_key: str, process: asyncio.subprocess.Process) -> None:
    """Register a running process for a session."""
    _running_processes[session_key] = process


def unregister_process(session_key: str) -> None:
    """Unregister a process for a session."""
    _running_processes.pop(session_key, None)


def cancel_process(session_key: str) -> bool:
    """Cancel a running process for a session.

    Returns True if a process was found and killed, False otherwise.
    """
    process = _running_processes.get(session_key)
    if process and process.returncode is None:
        process.kill()
        logger.info("Cancelled Claude Code process for session %s", session_key)
        return True
    return False


def is_process_running(session_key: str) -> bool:
    """Check if a process is currently running for a session."""
    process = _running_processes.get(session_key)
    return process is not None and process.returncode is None


async def run_claude(
    working_directory: str,
    message: str,
    extra_arguments: list[str] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    session_key: str | None = None,
    model: str | None = None,
) -> str:
    """Run Claude Code CLI as a subprocess and return its output.

    Args:
        working_directory: Working directory for Claude Code.
        message: The prompt message to send.
        extra_arguments: Additional CLI arguments from bot config.
        timeout: Maximum execution time in seconds.
        session_key: Optional key for process tracking (enables /cancel).
        model: Claude model to use (sonnet, opus, haiku).

    Returns:
        The text output from Claude Code.

    Raises:
        TimeoutError: If execution exceeds timeout.
        RuntimeError: If Claude Code returns a non-zero exit code.
        asyncio.CancelledError: If the process was cancelled via cancel_process.
    """
    claude_path = shutil.which("claude")
    if not claude_path:
        raise RuntimeError(
            "Claude Code CLI not found. Install: npm install -g @anthropic-ai/claude-code"
        )

    command = [
        claude_path,
        "-p",
        message,
        "--output-format",
        "text",
    ]

    if model:
        command.extend(["--model", model])

    if extra_arguments:
        command.extend(extra_arguments)

    logger.info("Running claude in %s: %s", working_directory, message[:100])

    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=working_directory,
    )

    if session_key:
        register_process(session_key, process)

    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        process.kill()
        await process.communicate()
        logger.error("Claude Code timed out after %ds", timeout)
        raise TimeoutError(f"Claude Code timed out after {timeout} seconds")
    finally:
        if session_key:
            unregister_process(session_key)

    if process.returncode == -9:
        raise asyncio.CancelledError("Claude Code was cancelled")

    output = stdout.decode("utf-8", errors="replace").strip()
    error_output = stderr.decode("utf-8", errors="replace").strip()

    if process.returncode != 0:
        logger.error("Claude Code failed (rc=%d): %s", process.returncode, error_output)
        raise RuntimeError(f"Claude Code exited with code {process.returncode}: {error_output}")

    if error_output:
        logger.warning("Claude Code stderr: %s", error_output[:200])

    return output
