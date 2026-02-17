"""cclaw CLI - Typer application entry point."""

import typer

app = typer.Typer(help="cclaw - Telegram + Claude Code AI assistant")
bot_app = typer.Typer(help="Bot management")
app.add_typer(bot_app, name="bot")
skill_app = typer.Typer(help="Skill management")
app.add_typer(skill_app, name="skill")


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
def skills() -> None:
    """List all skills (including unattached)."""
    from rich.console import Console
    from rich.table import Table

    from cclaw.skill import bots_using_skill, list_skills

    console = Console()
    all_skills = list_skills()

    if not all_skills:
        console.print("[yellow]No skills found. Run 'cclaw skill add' to create one.[/yellow]")
        return

    table = Table(title="All Skills")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Bots", style="dim")
    table.add_column("Description", style="dim")

    for skill in all_skills:
        skill_type_display = skill["type"] or "markdown"
        status = skill["status"]
        status_style = "green" if status == "active" else "yellow"
        connected_bots = ", ".join(bots_using_skill(skill["name"])) or "-"
        table.add_row(
            skill["name"],
            skill_type_display,
            f"[{status_style}]{status}[/{status_style}]",
            connected_bots,
            skill["description"],
        )

    console.print(table)


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


@skill_app.command("add")
def skill_add() -> None:
    """Create a new skill interactively."""
    from rich.console import Console

    from cclaw.skill import (
        VALID_SKILL_TYPES,
        create_skill_directory,
        default_skill_yaml,
        generate_skill_markdown,
        is_skill,
        save_skill_config,
    )

    console = Console()

    name = typer.prompt("Skill name")
    if is_skill(name):
        console.print(f"[red]Skill '{name}' already exists.[/red]")
        raise typer.Exit(1)

    description = typer.prompt("Description", default="")

    use_tools = typer.confirm("Does this skill require tools (CLI, MCP, browser)?", default=False)

    selected_type = None
    required_commands: list[str] = []
    environment_variables: list[str] = []

    if use_tools:
        type_choices = ", ".join(VALID_SKILL_TYPES)
        selected_type = typer.prompt(f"Skill type ({type_choices})")
        if selected_type not in VALID_SKILL_TYPES:
            console.print(f"[red]Invalid type: {selected_type}[/red]")
            raise typer.Exit(1)

        commands_input = typer.prompt("Required commands (comma-separated, or empty)", default="")
        if commands_input.strip():
            required_commands = [command.strip() for command in commands_input.split(",")]

        environment_variables_input = typer.prompt(
            "Environment variables (comma-separated, or empty)", default=""
        )
        if environment_variables_input.strip():
            environment_variables = [
                variable.strip() for variable in environment_variables_input.split(",")
            ]

    directory = create_skill_directory(name)

    skill_markdown = generate_skill_markdown(name, description)
    (directory / "SKILL.md").write_text(skill_markdown)

    if use_tools:
        config = default_skill_yaml(
            name=name,
            description=description,
            skill_type=selected_type,
            required_commands=required_commands if required_commands else None,
            environment_variables=environment_variables if environment_variables else None,
        )
        save_skill_config(name, config)
        console.print(
            f"[green]Skill '{name}' created (type: {selected_type}, status: inactive).[/green]"
        )
        console.print("Run [cyan]cclaw skill setup {name}[/cyan] to activate.")
    else:
        activate_skill_directly = True
        if activate_skill_directly:
            console.print(f"[green]Skill '{name}' created (markdown-only, active).[/green]")
        # No skill.yaml needed for markdown-only skills

    console.print(f"  Directory: {directory}")
    console.print(f"  Edit: [cyan]cclaw skill edit {name}[/cyan]")


@skill_app.command("list")
def skill_list() -> None:
    """List all skills."""
    from rich.console import Console
    from rich.table import Table

    from cclaw.skill import bots_using_skill, list_skills

    console = Console()
    skills = list_skills()

    if not skills:
        console.print("[yellow]No skills found. Run 'cclaw skill add' to create one.[/yellow]")
        return

    table = Table(title="Skills")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Bots", style="dim")
    table.add_column("Description", style="dim")

    for skill in skills:
        skill_type_display = skill["type"] or "markdown"
        status = skill["status"]
        status_style = "green" if status == "active" else "yellow"
        connected_bots = ", ".join(bots_using_skill(skill["name"])) or "-"
        table.add_row(
            skill["name"],
            skill_type_display,
            f"[{status_style}]{status}[/{status_style}]",
            connected_bots,
            skill["description"],
        )

    console.print(table)


@skill_app.command("remove")
def skill_remove(name: str) -> None:
    """Remove a skill."""
    from rich.console import Console

    from cclaw.skill import is_skill, remove_skill

    console = Console()

    if not is_skill(name):
        console.print(f"[red]Skill '{name}' not found.[/red]")
        raise typer.Exit(1)

    confirmed = typer.confirm(f"Remove skill '{name}'? This will detach it from all bots.")
    if not confirmed:
        console.print("[yellow]Cancelled.[/yellow]")
        return

    remove_skill(name)
    console.print(f"[green]Skill '{name}' removed.[/green]")


@skill_app.command("setup")
def skill_setup(name: str) -> None:
    """Set up a skill (check requirements and activate)."""
    from rich.console import Console

    from cclaw.skill import (
        activate_skill,
        check_skill_requirements,
        is_skill,
        load_skill_config,
        save_skill_config,
        skill_status,
    )

    console = Console()

    if not is_skill(name):
        console.print(f"[red]Skill '{name}' not found.[/red]")
        raise typer.Exit(1)

    if skill_status(name) == "active":
        console.print(f"[green]Skill '{name}' is already active.[/green]")
        return

    errors = check_skill_requirements(name)
    if errors:
        console.print(f"[red]Setup failed for '{name}':[/red]")
        for error in errors:
            console.print(f"  [red]- {error}[/red]")
        raise typer.Exit(1)

    # Prompt for environment variable values if needed
    config = load_skill_config(name)
    if config and config.get("environment_variables"):
        environment_variable_values = config.get("environment_variable_values", {})
        for variable in config["environment_variables"]:
            current = environment_variable_values.get(variable, "")
            value = typer.prompt(f"  {variable}", default=current)
            environment_variable_values[variable] = value
        config["environment_variable_values"] = environment_variable_values
        save_skill_config(name, config)

    activate_skill(name)
    console.print(f"[green]Skill '{name}' activated.[/green]")


@skill_app.command("test")
def skill_test(name: str) -> None:
    """Test a skill's requirements."""
    from rich.console import Console

    from cclaw.skill import check_skill_requirements, is_skill

    console = Console()

    if not is_skill(name):
        console.print(f"[red]Skill '{name}' not found.[/red]")
        raise typer.Exit(1)

    errors = check_skill_requirements(name)
    if errors:
        console.print(f"[red]Requirements check failed for '{name}':[/red]")
        for error in errors:
            console.print(f"  [red]- {error}[/red]")
    else:
        console.print(f"[green]All requirements met for '{name}'.[/green]")


@skill_app.command("edit")
def skill_edit(name: str) -> None:
    """Edit a skill's SKILL.md in the default editor."""
    import os
    import subprocess

    from rich.console import Console

    from cclaw.skill import is_skill, skill_directory

    console = Console()

    if not is_skill(name):
        console.print(f"[red]Skill '{name}' not found.[/red]")
        raise typer.Exit(1)

    skill_md_path = skill_directory(name) / "SKILL.md"
    editor = os.environ.get("EDITOR", "vi")
    subprocess.run([editor, str(skill_md_path)])
