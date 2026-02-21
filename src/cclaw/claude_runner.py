"""Claude Code subprocess runner."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
from contextlib import suppress
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 300
STREAMING_CURSOR = "\u258c"

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
    skill_names: list[str] | None = None,
    claude_session_id: str | None = None,
    resume_session: bool = False,
) -> str:
    """Run Claude Code CLI as a subprocess and return its output.

    Args:
        working_directory: Working directory for Claude Code.
        message: The prompt message to send.
        extra_arguments: Additional CLI arguments from bot config.
        timeout: Maximum execution time in seconds.
        session_key: Optional key for process tracking (enables /cancel).
        model: Claude model to use (sonnet, opus, haiku).
        skill_names: Optional list of skill names to inject MCP config and env vars.
        claude_session_id: Optional Claude Code session ID for continuity.
        resume_session: If True and claude_session_id is set, use --resume instead of --session-id.

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

    if resume_session and claude_session_id:
        command.extend(["--resume", claude_session_id])
    elif claude_session_id:
        command.extend(["--session-id", claude_session_id])

    if model:
        command.extend(["--model", model])

    if extra_arguments:
        command.extend(extra_arguments)

    # Inject MCP config and environment variables from skills
    environment = None
    if skill_names:
        from cclaw.skill import (
            collect_skill_allowed_tools,
            collect_skill_environment_variables,
            merge_mcp_configs,
        )

        mcp_config = merge_mcp_configs(skill_names)
        if mcp_config:
            mcp_json_path = str(Path(working_directory) / ".mcp.json")
            with open(mcp_json_path, "w") as mcp_file:
                json.dump(mcp_config, mcp_file, indent=2)

        skill_environment_variables = collect_skill_environment_variables(skill_names)
        if skill_environment_variables:
            environment = {**os.environ, **skill_environment_variables}

        allowed_tools = collect_skill_allowed_tools(skill_names)
        if allowed_tools:
            command.extend(["--allowedTools", ",".join(allowed_tools)])
            logger.info("Allowed tools from skills: %s", allowed_tools)

    logger.info("Running claude in %s: %s", working_directory, message[:100])

    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=working_directory,
        env=environment,
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


def _prepare_skill_environment(
    working_directory: str,
    skill_names: list[str] | None,
) -> dict[str, str] | None:
    """Prepare MCP config and environment variables for skills."""
    if not skill_names:
        return None

    from cclaw.skill import collect_skill_environment_variables, merge_mcp_configs

    mcp_config = merge_mcp_configs(skill_names)
    if mcp_config:
        mcp_json_path = str(Path(working_directory) / ".mcp.json")
        with open(mcp_json_path, "w") as mcp_file:
            json.dump(mcp_config, mcp_file, indent=2)

    skill_environment_variables = collect_skill_environment_variables(skill_names)
    if skill_environment_variables:
        return {**os.environ, **skill_environment_variables}

    return None


def _extract_text_delta(data: dict[str, Any]) -> str | None:
    """Extract text from a stream-json event line.

    Handles two event types:
    - stream_event with content_block_delta (token-level, --verbose mode)
    - assistant message with text content blocks (turn-level)
    """
    event_type = data.get("type")

    if event_type == "stream_event":
        event = data.get("event", {})
        if event.get("type") == "content_block_delta":
            delta = event.get("delta", {})
            if delta.get("type") == "text_delta":
                return delta.get("text", "")

    return None


def _extract_result_text(data: dict[str, Any]) -> str | None:
    """Extract the final result text from a result event."""
    if data.get("type") == "result":
        return data.get("result")
    return None


def _extract_assistant_text(data: dict[str, Any]) -> str | None:
    """Extract text from an assistant turn-level event (non-verbose mode)."""
    if data.get("type") == "assistant":
        message = data.get("message", {})
        content_blocks = message.get("content", [])
        texts = []
        for block in content_blocks:
            if block.get("type") == "text":
                texts.append(block.get("text", ""))
        if texts:
            return "".join(texts)
    return None


async def run_claude_streaming(
    working_directory: str,
    message: str,
    on_text_chunk: Callable[[str], Any] | None = None,
    extra_arguments: list[str] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    session_key: str | None = None,
    model: str | None = None,
    skill_names: list[str] | None = None,
    claude_session_id: str | None = None,
    resume_session: bool = False,
) -> str:
    """Run Claude Code CLI with streaming output.

    Uses --output-format stream-json --verbose --include-partial-messages
    to receive token-level text deltas. Calls on_text_chunk for each text
    chunk received. Returns the final complete text.

    If stream-json produces no result, falls back to accumulated text
    from streaming deltas or assistant turn events.

    Args:
        working_directory: Working directory for Claude Code.
        message: The prompt message to send.
        on_text_chunk: Async or sync callback for each text chunk.
        extra_arguments: Additional CLI arguments from bot config.
        timeout: Maximum execution time in seconds.
        session_key: Optional key for process tracking (enables /cancel).
        model: Claude model to use (sonnet, opus, haiku).
        skill_names: Optional list of skill names to inject MCP config and env vars.
        claude_session_id: Optional Claude Code session ID for continuity.
        resume_session: If True and claude_session_id is set, use --resume instead of --session-id.

    Returns:
        The complete text output from Claude Code.

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
        "stream-json",
        "--verbose",
        "--include-partial-messages",
    ]

    if resume_session and claude_session_id:
        command.extend(["--resume", claude_session_id])
    elif claude_session_id:
        command.extend(["--session-id", claude_session_id])

    if model:
        command.extend(["--model", model])

    if extra_arguments:
        command.extend(extra_arguments)

    environment = _prepare_skill_environment(working_directory, skill_names)

    if skill_names:
        from cclaw.skill import collect_skill_allowed_tools

        allowed_tools = collect_skill_allowed_tools(skill_names)
        if allowed_tools:
            command.extend(["--allowedTools", ",".join(allowed_tools)])
            logger.info("Allowed tools from skills: %s", allowed_tools)

    logger.info(
        "Running claude (streaming) in %s: %s",
        working_directory,
        message[:100],
    )

    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=working_directory,
        env=environment,
    )

    if session_key:
        register_process(session_key, process)

    accumulated_text = ""
    result_text: str | None = None

    async def read_stream() -> None:
        nonlocal accumulated_text, result_text

        while True:
            line = await process.stdout.readline()
            if not line:
                break

            line_text = line.decode("utf-8", errors="replace").strip()
            if not line_text:
                continue

            try:
                data = json.loads(line_text)
            except json.JSONDecodeError:
                logger.debug("Non-JSON line from stream: %s", line_text[:100])
                continue

            # Check for text delta (token-level streaming)
            text_delta = _extract_text_delta(data)
            if text_delta is not None:
                accumulated_text += text_delta
                if on_text_chunk and text_delta:
                    try:
                        result = on_text_chunk(text_delta)
                        if asyncio.iscoroutine(result):
                            await result
                    except Exception as callback_error:
                        logger.debug(
                            "Stream chunk callback error: %s",
                            callback_error,
                        )

            # Check for assistant turn text (fallback for non-verbose)
            assistant_text = _extract_assistant_text(data)
            if assistant_text is not None and not accumulated_text:
                accumulated_text = assistant_text
                if on_text_chunk:
                    with suppress(Exception):
                        result = on_text_chunk(assistant_text)
                        if asyncio.iscoroutine(result):
                            await result

            # Check for final result
            final = _extract_result_text(data)
            if final is not None:
                result_text = final

    try:
        await asyncio.wait_for(read_stream(), timeout=timeout)
        await process.wait()
    except asyncio.TimeoutError:
        process.kill()
        with suppress(Exception):
            await process.communicate()
        logger.error("Claude Code (streaming) timed out after %ds", timeout)
        raise TimeoutError(f"Claude Code timed out after {timeout} seconds")
    finally:
        if session_key:
            unregister_process(session_key)

    if process.returncode == -9:
        raise asyncio.CancelledError("Claude Code was cancelled")

    # Read any remaining stderr
    stderr_data = b""
    if process.stderr:
        with suppress(Exception):
            stderr_data = await process.stderr.read()
    error_output = stderr_data.decode("utf-8", errors="replace").strip()

    if process.returncode != 0:
        logger.error(
            "Claude Code (streaming) failed (rc=%d): %s",
            process.returncode,
            error_output,
        )
        raise RuntimeError(f"Claude Code exited with code {process.returncode}: {error_output}")

    if error_output:
        logger.warning("Claude Code stderr: %s", error_output[:200])

    # Prefer result event text, fall back to accumulated streaming text
    final_text = result_text if result_text is not None else accumulated_text
    return final_text.strip()
