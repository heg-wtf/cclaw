"""cclaw CLI - Typer application entry point."""

import typer

app = typer.Typer(help="cclaw - Telegram + Claude Code AI assistant")
bot_app = typer.Typer(help="Bot management")
app.add_typer(bot_app, name="bot")
skill_app = typer.Typer(help="Skill management")
app.add_typer(skill_app, name="skill")
cron_app = typer.Typer(help="Cron job management")
app.add_typer(cron_app, name="cron")
heartbeat_app = typer.Typer(help="Heartbeat management")
app.add_typer(heartbeat_app, name="heartbeat")


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
        from cclaw.config import DEFAULT_MODEL, bot_directory, load_bot_config

        bot_config = load_bot_config(bot_entry["name"])
        telegram_username = bot_config.get("telegram_username", "N/A") if bot_config else "N/A"
        model = bot_config.get("model", DEFAULT_MODEL) if bot_config else DEFAULT_MODEL
        path = str(bot_directory(bot_entry["name"]))
        table.add_row(bot_entry["name"], model, telegram_username, path)

    console.print(table)


@bot_app.command("remove")
def bot_remove(name: str) -> None:
    """Remove a bot."""
    import shutil

    from rich.console import Console

    from cclaw.config import bot_directory as get_bot_directory
    from cclaw.config import load_config, save_config

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

    target_directory = get_bot_directory(name)
    if target_directory.exists():
        shutil.rmtree(target_directory)

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

    from cclaw.config import bot_directory, load_bot_config

    console = Console()
    bot_config = load_bot_config(name)

    if not bot_config:
        console.print(f"[red]Bot '{name}' not found.[/red]")
        raise typer.Exit(1)

    bot_yaml_path = bot_directory(name) / "bot.yaml"
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


# --- Cron subcommands ---


@cron_app.command("list")
def cron_list(bot: str = typer.Argument(help="Bot name")) -> None:
    """List cron jobs for a bot."""
    from rich.console import Console
    from rich.table import Table

    from cclaw.config import load_bot_config
    from cclaw.cron import list_cron_jobs, next_run_time

    console = Console()

    if not load_bot_config(bot):
        console.print(f"[red]Bot '{bot}' not found.[/red]")
        raise typer.Exit(1)

    jobs = list_cron_jobs(bot)
    if not jobs:
        console.print(f"[yellow]No cron jobs for '{bot}'. Run 'cclaw cron add {bot}'.[/yellow]")
        return

    table = Table(title=f"Cron Jobs - {bot}")
    table.add_column("Name", style="cyan")
    table.add_column("Schedule", style="magenta")
    table.add_column("Message", style="dim", max_width=40)
    table.add_column("Next Run", style="green")
    table.add_column("Status", style="yellow")

    for job in jobs:
        schedule_display = job.get("schedule") or f"at: {job.get('at', 'N/A')}"
        enabled = job.get("enabled", True)
        status = "enabled" if enabled else "disabled"
        status_style = "green" if enabled else "red"

        next_time = next_run_time(job) if enabled else None
        next_display = next_time.strftime("%Y-%m-%d %H:%M UTC") if next_time else "-"

        message = job.get("message", "")
        if len(message) > 40:
            message = message[:37] + "..."

        table.add_row(
            job.get("name", ""),
            schedule_display,
            message,
            next_display,
            f"[{status_style}]{status}[/{status_style}]",
        )

    console.print(table)


@cron_app.command("add")
def cron_add(bot: str = typer.Argument(help="Bot name")) -> None:
    """Add a cron job to a bot interactively."""
    from rich.console import Console

    from cclaw.config import load_bot_config
    from cclaw.cron import (
        add_cron_job,
        get_cron_job,
        parse_one_shot_time,
        validate_cron_schedule,
    )

    console = Console()

    if not load_bot_config(bot):
        console.print(f"[red]Bot '{bot}' not found.[/red]")
        raise typer.Exit(1)

    name = typer.prompt("Job name")
    if get_cron_job(bot, name):
        console.print(f"[red]Job '{name}' already exists.[/red]")
        raise typer.Exit(1)

    use_one_shot = typer.confirm("One-shot (run once at specific time)?", default=False)

    job: dict = {"name": name, "enabled": True}

    if use_one_shot:
        at_value = typer.prompt("Run at (ISO datetime or duration like 30m/2h/1d)")
        parsed = parse_one_shot_time(at_value)
        if not parsed:
            console.print(f"[red]Invalid time: {at_value}[/red]")
            raise typer.Exit(1)
        job["at"] = at_value
        delete_after = typer.confirm("Delete after run?", default=True)
        job["delete_after_run"] = delete_after
    else:
        schedule = typer.prompt("Cron schedule (e.g. '0 9 * * *' for daily 9am)")
        if not validate_cron_schedule(schedule):
            console.print(f"[red]Invalid cron expression: {schedule}[/red]")
            raise typer.Exit(1)
        job["schedule"] = schedule

    message = typer.prompt("Message to send to Claude")
    job["message"] = message

    skills_input = typer.prompt("Skills (comma-separated, or empty)", default="")
    if skills_input.strip():
        job["skills"] = [skill.strip() for skill in skills_input.split(",")]

    model_input = typer.prompt("Model (sonnet/opus/haiku, or empty for bot default)", default="")
    if model_input.strip():
        from cclaw.config import is_valid_model

        if not is_valid_model(model_input.strip()):
            console.print(f"[red]Invalid model: {model_input}[/red]")
            raise typer.Exit(1)
        job["model"] = model_input.strip()

    add_cron_job(bot, job)
    console.print(f"[green]Cron job '{name}' added to '{bot}'.[/green]")


@cron_app.command("remove")
def cron_remove(
    bot: str = typer.Argument(help="Bot name"),
    job: str = typer.Argument(help="Job name"),
) -> None:
    """Remove a cron job."""
    from rich.console import Console

    from cclaw.cron import remove_cron_job

    console = Console()

    if not remove_cron_job(bot, job):
        console.print(f"[red]Job '{job}' not found in bot '{bot}'.[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Job '{job}' removed from '{bot}'.[/green]")


@cron_app.command("enable")
def cron_enable(
    bot: str = typer.Argument(help="Bot name"),
    job: str = typer.Argument(help="Job name"),
) -> None:
    """Enable a cron job."""
    from rich.console import Console

    from cclaw.cron import enable_cron_job

    console = Console()

    if not enable_cron_job(bot, job):
        console.print(f"[red]Job '{job}' not found in bot '{bot}'.[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Job '{job}' enabled.[/green]")


@cron_app.command("disable")
def cron_disable(
    bot: str = typer.Argument(help="Bot name"),
    job: str = typer.Argument(help="Job name"),
) -> None:
    """Disable a cron job."""
    from rich.console import Console

    from cclaw.cron import disable_cron_job

    console = Console()

    if not disable_cron_job(bot, job):
        console.print(f"[red]Job '{job}' not found in bot '{bot}'.[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Job '{job}' disabled.[/green]")


@cron_app.command("run")
def cron_run(
    bot: str = typer.Argument(help="Bot name"),
    job: str = typer.Argument(help="Job name"),
) -> None:
    """Run a cron job immediately (for testing)."""
    import asyncio

    from rich.console import Console

    from cclaw.claude_runner import run_claude
    from cclaw.config import DEFAULT_MODEL, load_bot_config
    from cclaw.cron import cron_session_directory, get_cron_job

    console = Console()

    bot_config = load_bot_config(bot)
    if not bot_config:
        console.print(f"[red]Bot '{bot}' not found.[/red]")
        raise typer.Exit(1)

    cron_job = get_cron_job(bot, job)
    if not cron_job:
        console.print(f"[red]Job '{job}' not found in bot '{bot}'.[/red]")
        raise typer.Exit(1)

    message = cron_job.get("message", "")
    model = cron_job.get("model") or bot_config.get("model", DEFAULT_MODEL)
    job_skills = cron_job.get("skills") or bot_config.get("skills", [])
    command_timeout = bot_config.get("command_timeout", 300)
    working_directory = str(cron_session_directory(bot, job))

    console.print(f"[cyan]Running job '{job}'...[/cyan]")
    console.print(f"  Message: {message}")
    console.print(f"  Model: {model}")

    async def _run() -> str:
        return await run_claude(
            working_directory=working_directory,
            message=message,
            timeout=command_timeout,
            session_key=f"cron:{bot}:{job}",
            model=model,
            skill_names=job_skills if job_skills else None,
        )

    try:
        response = asyncio.run(_run())
        console.print(f"\n[green]Result:[/green]\n{response}")
    except Exception as error:
        console.print(f"[red]Error: {error}[/red]")
        raise typer.Exit(1)


# --- Heartbeat subcommands ---


@heartbeat_app.command("status")
def heartbeat_status() -> None:
    """Show heartbeat status for all bots."""
    from rich.console import Console
    from rich.table import Table

    from cclaw.config import DEFAULT_MODEL, load_bot_config, load_config
    from cclaw.heartbeat import get_heartbeat_config

    console = Console()
    config = load_config()

    if not config or not config.get("bots"):
        console.print("[yellow]No bots configured.[/yellow]")
        return

    table = Table(title="Heartbeat Status")
    table.add_column("Bot", style="cyan")
    table.add_column("Enabled", style="green")
    table.add_column("Interval", style="magenta")
    table.add_column("Active Hours", style="dim")
    table.add_column("Model", style="yellow")

    for bot_entry in config["bots"]:
        name = bot_entry["name"]
        bot_config = load_bot_config(name)
        if not bot_config:
            continue

        heartbeat_config = get_heartbeat_config(name)
        enabled = heartbeat_config.get("enabled", False)
        interval = heartbeat_config.get("interval_minutes", 30)
        active_hours = heartbeat_config.get("active_hours", {})
        start = active_hours.get("start", "07:00")
        end = active_hours.get("end", "23:00")
        model = bot_config.get("model", DEFAULT_MODEL)

        enabled_display = "[green]on[/green]" if enabled else "[red]off[/red]"
        table.add_row(name, enabled_display, f"{interval}m", f"{start}-{end}", model)

    console.print(table)


@heartbeat_app.command("enable")
def heartbeat_enable(bot: str = typer.Argument(help="Bot name")) -> None:
    """Enable heartbeat for a bot."""
    from rich.console import Console

    from cclaw.config import load_bot_config
    from cclaw.heartbeat import enable_heartbeat

    console = Console()

    if not load_bot_config(bot):
        console.print(f"[red]Bot '{bot}' not found.[/red]")
        raise typer.Exit(1)

    if enable_heartbeat(bot):
        console.print(f"[green]Heartbeat enabled for '{bot}'.[/green]")
    else:
        console.print(f"[red]Failed to enable heartbeat for '{bot}'.[/red]")
        raise typer.Exit(1)


@heartbeat_app.command("disable")
def heartbeat_disable(bot: str = typer.Argument(help="Bot name")) -> None:
    """Disable heartbeat for a bot."""
    from rich.console import Console

    from cclaw.config import load_bot_config
    from cclaw.heartbeat import disable_heartbeat

    console = Console()

    if not load_bot_config(bot):
        console.print(f"[red]Bot '{bot}' not found.[/red]")
        raise typer.Exit(1)

    if disable_heartbeat(bot):
        console.print(f"[green]Heartbeat disabled for '{bot}'.[/green]")
    else:
        console.print(f"[red]Failed to disable heartbeat for '{bot}'.[/red]")
        raise typer.Exit(1)


@heartbeat_app.command("run")
def heartbeat_run(bot: str = typer.Argument(help="Bot name")) -> None:
    """Run heartbeat immediately (for testing)."""
    import asyncio

    from rich.console import Console

    from cclaw.claude_runner import run_claude
    from cclaw.config import DEFAULT_MODEL, load_bot_config
    from cclaw.heartbeat import (
        HEARTBEAT_OK_MARKER,
        heartbeat_session_directory,
        load_heartbeat_markdown,
    )

    console = Console()

    bot_config = load_bot_config(bot)
    if not bot_config:
        console.print(f"[red]Bot '{bot}' not found.[/red]")
        raise typer.Exit(1)

    heartbeat_content = load_heartbeat_markdown(bot)
    if not heartbeat_content:
        console.print(
            f"[yellow]No HEARTBEAT.md found. Run 'cclaw heartbeat enable {bot}' first.[/yellow]"
        )
        raise typer.Exit(1)

    model = bot_config.get("model", DEFAULT_MODEL)
    attached_skills = bot_config.get("skills", [])
    command_timeout = bot_config.get("command_timeout", 300)
    working_directory = str(heartbeat_session_directory(bot))

    message = f"다음 체크리스트를 확인하고 결과를 알려주세요.\n\n{heartbeat_content}"

    console.print(f"[cyan]Running heartbeat for '{bot}'...[/cyan]")
    console.print(f"  Model: {model}")

    async def _run() -> str:
        return await run_claude(
            working_directory=working_directory,
            message=message,
            timeout=command_timeout,
            session_key=f"heartbeat:{bot}",
            model=model,
            skill_names=attached_skills if attached_skills else None,
        )

    try:
        response = asyncio.run(_run())
        if HEARTBEAT_OK_MARKER in response:
            console.print("\n[green]Result: HEARTBEAT_OK (no notification needed)[/green]")
        else:
            console.print("\n[yellow]Result: notification would be sent[/yellow]")
        console.print(f"\n{response}")
    except Exception as error:
        console.print(f"[red]Error: {error}[/red]")
        raise typer.Exit(1)


@heartbeat_app.command("edit")
def heartbeat_edit(bot: str = typer.Argument(help="Bot name")) -> None:
    """Edit HEARTBEAT.md for a bot."""
    import os
    import subprocess

    from rich.console import Console

    from cclaw.config import load_bot_config
    from cclaw.heartbeat import (
        default_heartbeat_content,
        heartbeat_session_directory,
    )

    console = Console()

    if not load_bot_config(bot):
        console.print(f"[red]Bot '{bot}' not found.[/red]")
        raise typer.Exit(1)

    session_directory = heartbeat_session_directory(bot)
    heartbeat_md_path = session_directory / "HEARTBEAT.md"

    if not heartbeat_md_path.exists():
        heartbeat_md_path.write_text(default_heartbeat_content())

    editor = os.environ.get("EDITOR", "vi")
    subprocess.run([editor, str(heartbeat_md_path)])
