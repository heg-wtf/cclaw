"""Tests for cclaw.claude_runner module."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cclaw.claude_runner import run_claude

MOCK_SUBPROCESS = "cclaw.claude_runner.asyncio.create_subprocess_exec"


@pytest.mark.asyncio
async def test_run_claude_success():
    """run_claude returns stdout on success."""
    mock_process = MagicMock()
    mock_process.communicate = AsyncMock(return_value=(b"Hello from Claude", b""))
    mock_process.returncode = 0
    mock_process.kill = MagicMock()

    with patch(MOCK_SUBPROCESS, new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_process
        result = await run_claude("/tmp/test", "Hello")

    assert result == "Hello from Claude"
    mock_exec.assert_called_once()
    call_args = mock_exec.call_args[0]
    assert any("claude" in str(arg) for arg in call_args)
    assert "-p" in call_args
    assert "Hello" in call_args


@pytest.mark.asyncio
async def test_run_claude_with_extra_arguments():
    """run_claude passes extra_arguments to command."""
    mock_process = MagicMock()
    mock_process.communicate = AsyncMock(return_value=(b"output", b""))
    mock_process.returncode = 0

    with patch(MOCK_SUBPROCESS, new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_process
        await run_claude("/tmp/test", "Hello", extra_arguments=["--verbose"])

    call_args = mock_exec.call_args[0]
    assert "--verbose" in call_args


@pytest.mark.asyncio
async def test_run_claude_timeout():
    """run_claude raises TimeoutError on timeout."""
    mock_process = MagicMock()
    mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
    mock_process.kill = MagicMock()

    mock_process.communicate = AsyncMock(side_effect=[asyncio.TimeoutError(), (b"", b"")])

    with patch(MOCK_SUBPROCESS, new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_process

        with patch(
            "cclaw.claude_runner.asyncio.wait_for",
            side_effect=asyncio.TimeoutError(),
        ):
            mock_process.communicate = AsyncMock(return_value=(b"", b""))
            with pytest.raises(TimeoutError, match="timed out"):
                await run_claude("/tmp/test", "Hello", timeout=1)

    mock_process.kill.assert_called_once()


@pytest.mark.asyncio
async def test_run_claude_nonzero_exit():
    """run_claude raises RuntimeError on non-zero exit code."""
    mock_process = MagicMock()
    mock_process.communicate = AsyncMock(return_value=(b"", b"Error occurred"))
    mock_process.returncode = 1

    with patch(MOCK_SUBPROCESS, new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_process

        with pytest.raises(RuntimeError, match="exited with code 1"):
            await run_claude("/tmp/test", "Hello")


@pytest.mark.asyncio
async def test_run_claude_working_directory():
    """run_claude uses the specified working directory."""
    mock_process = MagicMock()
    mock_process.communicate = AsyncMock(return_value=(b"ok", b""))
    mock_process.returncode = 0

    with patch(MOCK_SUBPROCESS, new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_process
        await run_claude("/my/project", "Hello")

    call_kwargs = mock_exec.call_args[1]
    assert call_kwargs["cwd"] == "/my/project"
