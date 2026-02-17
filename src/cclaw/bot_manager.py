"""Bot lifecycle manager for cclaw."""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import subprocess
import sys
from pathlib import Path

from rich.console import Console

from cclaw.config import bot_directory, cclaw_home, load_bot_config, load_config
from cclaw.handlers import make_handlers, set_bot_commands
from cclaw.utils import setup_logging

logger = logging.getLogger(__name__)
console = Console()

LAUNCHD_LABEL = "com.cclaw.daemon"
PID_FILE_NAME = "cclaw.pid"


def _pid_file() -> Path:
    """Return path to PID file."""
    return cclaw_home() / PID_FILE_NAME


def _plist_path() -> Path:
    """Return path to launchd plist file."""
    return Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist"


async def _run_bots(bot_names: list[str] | None = None) -> None:
    """Run one or more bots with long polling."""
    from telegram.ext import Application

    config = load_config()
    if not config or not config.get("bots"):
        console.print("[red]No bots configured. Run 'cclaw init' first.[/red]")
        return

    settings = config.get("settings", {})
    log_level = settings.get("log_level", "INFO")
    setup_logging(log_level)

    bots_to_run = config["bots"]
    if bot_names:
        bots_to_run = [b for b in bots_to_run if b["name"] in bot_names]
        if not bots_to_run:
            console.print("[red]No matching bots found.[/red]")
            return

    applications = []

    for bot_entry in bots_to_run:
        name = bot_entry["name"]
        try:
            bot_config = load_bot_config(name)
            if not bot_config:
                console.print(f"[yellow]Skipping {name}: bot.yaml not found.[/yellow]")
                continue

            token = bot_config.get("telegram_token", "")
            if not token:
                console.print(f"[yellow]Skipping {name}: no token configured.[/yellow]")
                continue

            # Regenerate CLAUDE.md if skills are attached (to pick up any changes)
            if bot_config.get("skills"):
                from cclaw.skill import regenerate_bot_claude_md

                regenerate_bot_claude_md(name)

            bot_path = bot_directory(name)
            handlers = make_handlers(name, bot_path, bot_config)

            application = Application.builder().token(token).post_init(set_bot_commands).build()

            for handler in handlers:
                application.add_handler(handler)

            applications.append((name, application))
            logger.info("Prepared bot: %s", name)
        except Exception as error:
            console.print(f"[red]Error preparing {name}: {error}[/red]")
            logger.error("Failed to prepare bot %s: %s", name, error)

    if not applications:
        console.print("[red]No valid bots to start.[/red]")
        return

    console.print(f"Starting {len(applications)} bot(s)...")
    for name, _ in applications:
        console.print(f"  [green]OK[/green] {name}")

    pid_file = _pid_file()
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(os.getpid()))

    stop_event = asyncio.Event()

    loop = asyncio.get_event_loop()

    def signal_handler():
        logger.info("Shutdown signal received")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    started_applications = []
    cron_tasks = []
    try:
        for name, application in applications:
            try:
                await application.initialize()
                await application.start()
                await application.updater.start_polling(drop_pending_updates=True)
                started_applications.append((name, application))
            except Exception as error:
                console.print(f"[red]Failed to start {name}: {error}[/red]")
                logger.error("Failed to start bot %s: %s", name, error)
                try:
                    await application.shutdown()
                except Exception:
                    pass

        if not started_applications:
            console.print("[red]No bots started successfully.[/red]")
            return

        # Start cron schedulers for bots that have cron jobs
        from cclaw.cron import list_cron_jobs, run_cron_scheduler

        for name, application in started_applications:
            bot_config = load_bot_config(name)
            if not bot_config:
                continue
            jobs = list_cron_jobs(name)
            if jobs:
                task = asyncio.create_task(
                    run_cron_scheduler(name, bot_config, application, stop_event)
                )
                cron_tasks.append(task)
                console.print(f"  [green]CRON[/green] {name} ({len(jobs)} job(s))")

        console.print(f"\n{len(started_applications)} bot(s) running. Press Ctrl+C to stop.")
        await stop_event.wait()

    finally:
        console.print("\nStopping bots...")

        # Cancel cron tasks
        for task in cron_tasks:
            task.cancel()
        if cron_tasks:
            await asyncio.gather(*cron_tasks, return_exceptions=True)

        for name, application in started_applications:
            try:
                await application.updater.stop()
                await application.stop()
                await application.shutdown()
                logger.info("Stopped bot: %s", name)
            except Exception as error:
                logger.error("Error stopping %s: %s", name, error)

        if pid_file.exists():
            pid_file.unlink()

        console.print("[green]All bots stopped.[/green]")


def start_bots(bot_name: str | None = None, daemon: bool = False) -> None:
    """Start bot(s), optionally as a daemon."""
    if daemon:
        _start_daemon()
        return

    bot_names = [bot_name] if bot_name else None

    try:
        asyncio.run(_run_bots(bot_names))
    except KeyboardInterrupt:
        pass


def _start_daemon() -> None:
    """Start cclaw as a launchd daemon."""
    plist_path = _plist_path()
    plist_path.parent.mkdir(parents=True, exist_ok=True)

    # Find cclaw in the same venv bin directory
    venv_bin = Path(sys.executable).parent
    cclaw_executable = venv_bin / "cclaw"
    if not cclaw_executable.exists():
        cclaw_executable = Path(sys.executable)
        cclaw_arguments = [str(cclaw_executable), "-m", "cclaw.cli", "start"]
    else:
        cclaw_arguments = [str(cclaw_executable), "start"]

    log_directory = cclaw_home() / "logs"
    log_directory.mkdir(parents=True, exist_ok=True)

    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{LAUNCHD_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        {"".join(f"        <string>{arg}</string>{chr(10)}" for arg in cclaw_arguments)}    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{log_directory / "daemon-stdout.log"}</string>
    <key>StandardErrorPath</key>
    <string>{log_directory / "daemon-stderr.log"}</string>
</dict>
</plist>
"""

    plist_path.write_text(plist_content)

    subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
    result = subprocess.run(["launchctl", "load", str(plist_path)], capture_output=True, text=True)

    if result.returncode == 0:
        console.print("[green]Daemon started.[/green]")
        console.print(f"  Plist: {plist_path}")
        console.print(f"  Logs:  {log_directory}")
        console.print("\n  Stop with: cclaw stop")
    else:
        console.print(f"[red]Failed to start daemon: {result.stderr}[/red]")


def stop_bots() -> None:
    """Stop the running daemon or foreground process."""
    plist_path = _plist_path()

    if plist_path.exists():
        result = subprocess.run(
            ["launchctl", "unload", str(plist_path)],
            capture_output=True,
            text=True,
        )
        plist_path.unlink(missing_ok=True)
        if result.returncode == 0:
            console.print("[green]Daemon stopped.[/green]")
        else:
            console.print(f"[yellow]launchctl unload: {result.stderr.strip()}[/yellow]")

    pid_file = _pid_file()
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            console.print(f"[green]Sent SIGTERM to process {pid}.[/green]")
        except (ValueError, ProcessLookupError):
            pass
        pid_file.unlink(missing_ok=True)
    elif not plist_path.exists():
        console.print("[yellow]No running cclaw process found.[/yellow]")


def show_status() -> None:
    """Show the running status of cclaw."""
    from rich.table import Table

    config = load_config()

    pid_file = _pid_file()
    plist_path = _plist_path()

    if plist_path.exists():
        console.print("[green]Daemon: running (launchd)[/green]")
    elif pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, 0)
            console.print(f"[green]Process: running (PID {pid})[/green]")
        except (ValueError, ProcessLookupError):
            console.print("[yellow]Process: stale PID file[/yellow]")
            pid_file.unlink(missing_ok=True)
    else:
        console.print("[yellow]Status: not running[/yellow]")

    if not config or not config.get("bots"):
        console.print("[yellow]No bots configured.[/yellow]")
        return

    table = Table(title="Bot Status")
    table.add_column("Name", style="cyan")
    table.add_column("Telegram", style="green")
    table.add_column("Sessions", justify="right")

    for bot_entry in config["bots"]:
        name = bot_entry["name"]
        bot_config = load_bot_config(name)
        telegram_username = bot_config.get("telegram_username", "N/A") if bot_config else "N/A"

        session_directory = bot_directory(name) / "sessions"
        session_count = 0
        if session_directory.exists():
            session_count = len([d for d in session_directory.iterdir() if d.is_dir()])

        table.add_row(name, telegram_username, str(session_count))

    console.print(table)
