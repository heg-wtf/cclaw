"""cclaw CLI - Typer application entry point."""

import typer

app = typer.Typer(help="cclaw - Telegram + Claude Code AI assistant")
bot_app = typer.Typer(help="Bot management")
app.add_typer(bot_app, name="bot")


@app.command()
def init() -> None:
    """Run initial setup wizard."""
    from cclaw.onboarding import run_onboarding

    run_onboarding()


@app.command()
def start(
    bot: str = typer.Option(None, help="Start specific bot only"),
    daemon: bool = typer.Option(False, help="Run as background daemon"),
) -> None:
    """Start bot(s)."""
    from cclaw.bot_manager import start_bots

    start_bots(bot_name=bot, daemon=daemon)


@app.command()
def stop() -> None:
    """Stop daemon."""
    from cclaw.bot_manager import stop_bots

    stop_bots()


@app.command()
def status() -> None:
    """Show running status."""
    from cclaw.bot_manager import show_status

    show_status()


@app.command()
def doctor() -> None:
    """Check environment and configuration."""
    from cclaw.onboarding import run_doctor

    run_doctor()


@bot_app.command("add")
def bot_add() -> None:
    """Add a new bot."""
    from cclaw.onboarding import add_bot

    add_bot()


@bot_app.command("list")
def bot_list() -> None:
    """List all bots."""
    from rich.console import Console
    from rich.table import Table

    from cclaw.config import load_config

    console = Console()
    config = load_config()

    if not config or not config.get("bots"):
        console.print("[yellow]No bots configured. Run 'cclaw init' or 'cclaw bot add'.[/yellow]")
        return

    table = Table(title="Registered Bots")
    table.add_column("Name", style="cyan")
    table.add_column("Model", style="magenta")
    table.add_column("Telegram", style="green")
    table.add_column("Path", style="dim")

    for bot_entry in config["bots"]:
        from cclaw.config import DEFAULT_MODEL, cclaw_home, load_bot_config

        bot_config = load_bot_config(bot_entry["name"])
        telegram_username = bot_config.get("telegram_username", "N/A") if bot_config else "N/A"
        model = bot_config.get("model", DEFAULT_MODEL) if bot_config else DEFAULT_MODEL
        path = str(cclaw_home() / bot_entry["path"])
        table.add_row(bot_entry["name"], model, telegram_username, path)

    console.print(table)


@bot_app.command("remove")
def bot_remove(name: str) -> None:
    """Remove a bot."""
    import shutil

    from rich.console import Console

    from cclaw.config import cclaw_home, load_config, save_config

    console = Console()
    config = load_config()

    if not config or not config.get("bots"):
        console.print("[red]No bots configured.[/red]")
        raise typer.Exit(1)

    bot_entry = next((b for b in config["bots"] if b["name"] == name), None)
    if not bot_entry:
        console.print(f"[red]Bot '{name}' not found.[/red]")
        raise typer.Exit(1)

    confirmed = typer.confirm(f"Remove bot '{name}'? This will delete all data.")
    if not confirmed:
        console.print("[yellow]Cancelled.[/yellow]")
        return

    bot_directory = cclaw_home() / bot_entry["path"]
    if bot_directory.exists():
        shutil.rmtree(bot_directory)

    config["bots"] = [b for b in config["bots"] if b["name"] != name]
    save_config(config)

    console.print(f"[green]Bot '{name}' removed.[/green]")


@app.command()
def logs(
    lines: int = typer.Option(50, "--lines", "-n", help="Number of lines to show"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
) -> None:
    """Show today's log file."""
    import subprocess
    from datetime import datetime

    from rich.console import Console

    from cclaw.config import cclaw_home

    console = Console()
    log_directory = cclaw_home() / "logs"
    today = datetime.now().strftime("%y%m%d")
    log_file = log_directory / f"cclaw-{today}.log"

    if not log_file.exists():
        console.print("[yellow]No log file for today.[/yellow]")
        raise typer.Exit()

    command = ["tail", f"-n{lines}"]
    if follow:
        command.append("-f")
    command.append(str(log_file))

    try:
        subprocess.run(command)
    except KeyboardInterrupt:
        pass


@bot_app.command("model")
def bot_model(
    name: str = typer.Argument(help="Bot name"),
    model: str = typer.Argument(None, help="Model to set (sonnet/opus/haiku)"),
) -> None:
    """Show or change the model for a bot."""
    from rich.console import Console

    from cclaw.config import (
        DEFAULT_MODEL,
        VALID_MODELS,
        is_valid_model,
        load_bot_config,
        save_bot_config,
    )

    console = Console()
    bot_config = load_bot_config(name)
    if not bot_config:
        console.print(f"[red]Bot '{name}' not found.[/red]")
        raise typer.Exit(1)

    if model is None:
        current = bot_config.get("model", DEFAULT_MODEL)
        console.print(f"[cyan]{name}[/cyan] model: [magenta]{current}[/magenta]")
        return

    if not is_valid_model(model):
        console.print(f"[red]Invalid model: {model}[/red]")
        console.print(f"Available: {', '.join(VALID_MODELS)}")
        raise typer.Exit(1)

    bot_config["model"] = model
    save_bot_config(name, bot_config)
    console.print(f"[green]{name} model changed to {model}[/green]")


@bot_app.command("edit")
def bot_edit(name: str) -> None:
    """Edit bot configuration."""
    import subprocess

    from rich.console import Console

    from cclaw.config import cclaw_home, load_config

    console = Console()
    config = load_config()

    if not config or not config.get("bots"):
        console.print("[red]No bots configured.[/red]")
        raise typer.Exit(1)

    bot_entry = next((b for b in config["bots"] if b["name"] == name), None)
    if not bot_entry:
        console.print(f"[red]Bot '{name}' not found.[/red]")
        raise typer.Exit(1)

    bot_yaml_path = cclaw_home() / bot_entry["path"] / "bot.yaml"
    editor = "vi"
    subprocess.run([editor, str(bot_yaml_path)])
