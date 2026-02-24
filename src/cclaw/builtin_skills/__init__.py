"""Built-in skill registry for cclaw."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def builtin_skills_directory() -> Path:
    """Return the directory containing built-in skill templates."""
    return Path(__file__).parent


def list_builtin_skills() -> list[dict[str, Any]]:
    """List all available built-in skills.

    Scans subdirectories for those containing SKILL.md.
    Returns a list of dicts with name, description, and path.
    """
    directory = builtin_skills_directory()
    result = []

    for entry in sorted(directory.iterdir()):
        if entry.is_dir() and (entry / "SKILL.md").exists():
            description = ""
            skill_yaml_path = entry / "skill.yaml"
            if skill_yaml_path.exists():
                with open(skill_yaml_path) as file:
                    config = yaml.safe_load(file) or {}
                description = config.get("description", "")

            emoji = config.get("emoji", "") if skill_yaml_path.exists() else ""

            result.append(
                {
                    "name": entry.name,
                    "description": description,
                    "emoji": emoji,
                    "path": entry,
                }
            )

    return result


def get_builtin_skill_path(name: str) -> Path | None:
    """Return the path to a specific built-in skill template.

    Returns None if the skill does not exist.
    """
    path = builtin_skills_directory() / name
    if path.is_dir() and (path / "SKILL.md").exists():
        return path
    return None


def is_builtin_skill(name: str) -> bool:
    """Check if a built-in skill with the given name exists."""
    return get_builtin_skill_path(name) is not None
