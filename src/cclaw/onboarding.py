"""Onboarding and environment checking for cclaw."""

from __future__ import annotations

import asyncio
import shutil
import subprocess
from dataclasses import dataclass

import typer
from rich.console import Console
from rich.panel import Panel

from cclaw.config import (
    add_bot_to_config,
    bot_exists,
    cclaw_home,
    load_bot_config,
    load_config,
    save_bot_config,
)

console = Console()

MAXIMUM_TOKEN_RETRY = 3


@dataclass
class EnvironmentCheckResult:
    """Result of an environment check."""

    name: str
    available: bool
    version: str
    message: str


def check_claude_code() -> EnvironmentCheckResult:
    """Check if Claude Code CLI is installed."""
    path = shutil.which("claude")
    if not path:
        return EnvironmentCheckResult(
            name="Claude Code",
            available=False,
            version="",
            message="Claude Code is not installed.\n\n"
            "  Install:\n"
            "    npm install -g @anthropic-ai/claude-code\n\n"
            "  Then run again: cclaw init",
        )
    try:
        result = subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=10)
        version = result.stdout.strip() or result.stderr.strip()
    except (subprocess.TimeoutExpired, OSError):
        version = "unknown"

    return EnvironmentCheckResult(name="Claude Code", available=True, version=version, message="")


def check_node() -> EnvironmentCheckResult:
    """Check if Node.js is installed."""
    path = shutil.which("node")
    if not path:
        return EnvironmentCheckResult(
            name="Node.js",
            available=False,
            version="",
            message="Node.js is not installed. Required for Claude Code.",
        )
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=10)
        version = result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        version = "unknown"

    return EnvironmentCheckResult(name="Node.js", available=True, version=version, message="")


def check_python() -> EnvironmentCheckResult:
    """Check Python version."""
    import sys

    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    return EnvironmentCheckResult(name="Python", available=True, version=version, message="")


def run_environment_checks() -> list[EnvironmentCheckResult]:
    """Run all environment checks and return results."""
    return [check_python(), check_node(), check_claude_code()]


def display_environment_checks(checks: list[EnvironmentCheckResult]) -> bool:
    """Display environment check results. Returns True if all passed."""
    console.print("\nChecking environment...")
    all_passed = True
    for check in checks:
        if check.available:
            console.print(f"  [green]OK[/green] {check.name} {check.version}")
        else:
            console.print(f"  [red]FAIL[/red] {check.name}")
            if check.message:
                console.print(f"\n  {check.message}")
            all_passed = False
    return all_passed


async def validate_telegram_token(token: str) -> dict | None:
    """Validate a Telegram bot token. Returns bot info dict or None."""
    from telegram import Bot

    try:
        bot = Bot(token=token)
        bot_info = await bot.get_me()
        return {
            "username": f"@{bot_info.username}",
            "botname": bot_info.first_name,
        }
    except Exception:
        return None


def prompt_telegram_token() -> tuple[str, dict]:
    """Prompt user for Telegram bot token with retry. Returns (token, bot_info)."""
    console.print("\n[bold]Connecting Telegram bot.[/bold]")
    console.print()
    console.print("  1. Send a DM to @BotFather on Telegram.")
    console.print("  2. Create a bot with the /newbot command.")
    console.print("  3. Enter the issued token below.")
    console.print()

    for attempt in range(MAXIMUM_TOKEN_RETRY):
        token = console.input("Bot Token: ").strip()
        console.print("Verifying token...")

        bot_info = asyncio.run(validate_telegram_token(token))
        if bot_info:
            console.print(
                f"[green]OK[/green] Bot verified: {bot_info['username']} ({bot_info['botname']})"
            )
            return token, bot_info

        remaining = MAXIMUM_TOKEN_RETRY - attempt - 1
        if remaining > 0:
            console.print(f"[red]Invalid token. {remaining} attempts remaining.[/red]")
        else:
            console.print("[red]Maximum retry attempts exceeded.[/red]")
            raise typer.Exit(1)

    raise typer.Exit(1)


def prompt_bot_profile() -> dict:
    """Prompt user for bot profile information. Returns profile dict."""
    console.print("\n[bold]Setting up bot profile.[/bold]\n")

    while True:
        name = console.input("Bot name (English, used as directory name): ").strip()
        name = name.strip().lower().replace(" ", "-")
        if not name.isascii() or not name.replace("-", "").isalnum():
            console.print("[red]Use only English letters, numbers, and hyphens.[/red]")
            continue
        if bot_exists(name):
            console.print(f"[red]Bot '{name}' already exists.[/red]")
            continue
        break

    personality = console.input("Bot personality: ").strip()
    description = console.input("Bot role/tasks: ").strip()

    return {
        "name": name,
        "personality": personality,
        "description": description,
    }


def create_bot(token: str, bot_info: dict, profile: dict) -> None:
    """Create bot configuration files."""
    bot_config = {
        "telegram_token": token,
        "telegram_username": bot_info["username"],
        "telegram_botname": bot_info["botname"],
        "description": profile["description"],
        "personality": profile["personality"],
        "allowed_users": [],
        "claude_args": [],
    }

    save_bot_config(profile["name"], bot_config)
    add_bot_to_config(profile["name"])

    home = cclaw_home()
    console.print()
    console.print(
        Panel(
            f"[green]OK[/green] {profile['name']} created!\n\n"
            f"  Name:      {profile['name']}\n"
            f"  Personality: {profile['personality']}\n"
            f"  Role:      {profile['description']}\n"
            f"  Path:      {home / 'bots' / profile['name']}\n"
            f"  Telegram:  {bot_info['username']}\n\n"
            f"  Start the bot: cclaw start",
            title=profile["name"],
        )
    )


def run_onboarding() -> None:
    """Run the full onboarding flow."""
    console.print("[bold]Starting cclaw initial setup.[/bold]")

    checks = run_environment_checks()
    if not display_environment_checks(checks):
        raise typer.Exit(1)

    console.print("\n[green]Environment check passed![/green]")

    token, bot_info = prompt_telegram_token()
    profile = prompt_bot_profile()
    create_bot(token, bot_info, profile)


def add_bot() -> None:
    """Add a new bot (reuses onboarding Steps 2+3)."""
    token, bot_info = prompt_telegram_token()
    profile = prompt_bot_profile()
    create_bot(token, bot_info, profile)


def run_doctor() -> None:
    """Run environment and configuration diagnostics."""
    console.print("[bold]cclaw doctor[/bold]\n")

    checks = run_environment_checks()
    display_environment_checks(checks)

    console.print()

    config = load_config()
    if config is None:
        console.print("[yellow]No config.yaml found. Run 'cclaw init' first.[/yellow]")
        return

    console.print("[green]OK[/green] config.yaml found")
    console.print(f"  Log level: {config.get('settings', {}).get('log_level', 'N/A')}")

    bots = config.get("bots", [])
    if not bots:
        console.print("[yellow]No bots configured.[/yellow]")
        return

    console.print(f"\n[bold]Bots ({len(bots)}):[/bold]")

    for bot_entry in bots:
        name = bot_entry["name"]
        bot_config = load_bot_config(name)
        if not bot_config:
            console.print(f"  [red]FAIL[/red] {name}: bot.yaml missing")
            continue

        token = bot_config.get("telegram_token", "")
        bot_info = asyncio.run(validate_telegram_token(token))
        if bot_info:
            console.print(f"  [green]OK[/green] {name}: token valid ({bot_info['username']})")
        else:
            console.print(f"  [red]FAIL[/red] {name}: token invalid")

        session_directory = cclaw_home() / bot_entry["path"] / "sessions"
        if session_directory.exists():
            session_count = len(list(session_directory.iterdir()))
            console.print(f"       Sessions: {session_count}")
        else:
            console.print("       Sessions: 0")
