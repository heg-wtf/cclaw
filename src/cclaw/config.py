"""Configuration management for cclaw."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def cclaw_home() -> Path:
    """Return the cclaw home directory. Defaults to ~/.cclaw/, overridable via CCLAW_HOME."""
    return Path(os.environ.get("CCLAW_HOME", Path.home() / ".cclaw"))


def ensure_home() -> Path:
    """Ensure the cclaw home directory exists and return its path."""
    home = cclaw_home()
    home.mkdir(parents=True, exist_ok=True)
    return home


def config_path() -> Path:
    """Return path to the global config.yaml."""
    return cclaw_home() / "config.yaml"


def load_config() -> dict[str, Any] | None:
    """Load the global config.yaml. Returns None if it doesn't exist."""
    path = config_path()
    if not path.exists():
        return None
    with open(path) as file:
        return yaml.safe_load(file)


def save_config(config: dict[str, Any]) -> None:
    """Save the global config.yaml."""
    ensure_home()
    with open(config_path(), "w") as file:
        yaml.dump(config, file, default_flow_style=False, allow_unicode=True)


def bot_directory(name: str) -> Path:
    """Return the bot directory path."""
    return cclaw_home() / "bots" / name


def load_bot_config(name: str) -> dict[str, Any] | None:
    """Load a bot's bot.yaml. Returns None if it doesn't exist."""
    path = bot_directory(name) / "bot.yaml"
    if not path.exists():
        return None
    with open(path) as file:
        return yaml.safe_load(file)


def save_bot_config(name: str, bot_config: dict[str, Any]) -> None:
    """Save a bot's bot.yaml and generate CLAUDE.md."""
    directory = bot_directory(name)
    directory.mkdir(parents=True, exist_ok=True)

    sessions_directory = directory / "sessions"
    sessions_directory.mkdir(exist_ok=True)

    with open(directory / "bot.yaml", "w") as file:
        yaml.dump(bot_config, file, default_flow_style=False, allow_unicode=True)

    # Lazy import to avoid circular dependency with skill module
    from cclaw.skill import compose_claude_md

    claude_md_content = compose_claude_md(
        bot_name=name,
        personality=bot_config.get("personality", ""),
        description=bot_config.get("description", ""),
        skill_names=bot_config.get("skills", []),
        bot_path=directory,
    )
    with open(directory / "CLAUDE.md", "w") as file:
        file.write(claude_md_content)


def generate_claude_md(name: str, personality: str, description: str) -> str:
    """Generate CLAUDE.md content for a bot."""
    return f"""# {name}

## Personality
{personality}

## Role
{description}

## Rules
- Respond in Korean.
- Save generated files to the workspace/ directory.
- Always ask for confirmation before executing dangerous commands (delete, restart, etc.).
"""


def default_config() -> dict[str, Any]:
    """Return a default config structure."""
    return {
        "bots": [],
        "settings": {
            "log_level": "INFO",
            "command_timeout": 300,
        },
    }


def add_bot_to_config(name: str) -> None:
    """Add a bot entry to the global config."""
    config = load_config() or default_config()
    if "bots" not in config:
        config["bots"] = []

    existing = [b for b in config["bots"] if b["name"] == name]
    if not existing:
        config["bots"].append({"name": name, "path": str(bot_directory(name))})

    save_config(config)


def remove_bot_from_config(name: str) -> None:
    """Remove a bot entry from the global config."""
    config = load_config()
    if not config or "bots" not in config:
        return
    config["bots"] = [b for b in config["bots"] if b["name"] != name]
    save_config(config)


def load_cron_config(name: str) -> dict[str, Any]:
    """Load a bot's cron.yaml. Returns empty config if not found."""
    path = bot_directory(name) / "cron.yaml"
    if not path.exists():
        return {"jobs": []}
    with open(path) as file:
        data = yaml.safe_load(file)
    if not data or "jobs" not in data:
        return {"jobs": []}
    return data


def save_cron_config(name: str, config: dict[str, Any]) -> None:
    """Save a bot's cron.yaml."""
    path = bot_directory(name) / "cron.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as file:
        yaml.dump(config, file, default_flow_style=False, allow_unicode=True)


def cron_session_directory(bot_name: str, job_name: str) -> Path:
    """Return the cron session directory path for a job."""
    return bot_directory(bot_name) / "cron_sessions" / job_name


VALID_MODELS = ["sonnet", "opus", "haiku"]
MODEL_VERSIONS: dict[str, str] = {
    "sonnet": "4.5",
    "opus": "4.6",
    "haiku": "3.5",
}
DEFAULT_MODEL = "sonnet"
DEFAULT_STREAMING = True


def is_valid_model(model: str) -> bool:
    """Check if the model name is valid."""
    return model in VALID_MODELS


def model_display_name(model: str) -> str:
    """Return model name with version (e.g. 'opus 4.6')."""
    version = MODEL_VERSIONS.get(model, "")
    return f"{model} {version}" if version else model


def bot_exists(name: str) -> bool:
    """Check if a bot with this name already exists."""
    config = load_config()
    if not config or "bots" not in config:
        return False
    return any(b["name"] == name for b in config["bots"])
