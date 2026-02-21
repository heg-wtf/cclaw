"""Tests for built-in skill registry and installation."""

from __future__ import annotations

import pytest
import yaml

from cclaw.builtin_skills import (
    builtin_skills_directory,
    get_builtin_skill_path,
    is_builtin_skill,
    list_builtin_skills,
)
from cclaw.skill import (
    check_skill_requirements,
    install_builtin_skill,
    is_skill,
    list_skills,
    load_skill_config,
    save_skill_config,
    skill_status,
)


@pytest.fixture
def temp_cclaw_home(tmp_path, monkeypatch):
    """Set CCLAW_HOME to a temporary directory."""
    home = tmp_path / ".cclaw"
    monkeypatch.setenv("CCLAW_HOME", str(home))
    return home


# --- Registry Tests ---


def test_builtin_skills_directory_exists():
    """builtin_skills_directory returns a real directory."""
    directory = builtin_skills_directory()
    assert directory.exists()
    assert directory.is_dir()


def test_list_builtin_skills_returns_imessage():
    """list_builtin_skills includes the imessage skill."""
    skills = list_builtin_skills()
    names = [skill["name"] for skill in skills]
    assert "imessage" in names

    imessage = next(skill for skill in skills if skill["name"] == "imessage")
    assert imessage["description"] != ""
    assert imessage["path"].is_dir()


def test_get_builtin_skill_path_exists():
    """get_builtin_skill_path returns path for existing skill."""
    path = get_builtin_skill_path("imessage")
    assert path is not None
    assert (path / "SKILL.md").exists()
    assert (path / "skill.yaml").exists()


def test_get_builtin_skill_path_nonexistent():
    """get_builtin_skill_path returns None for unknown skill."""
    assert get_builtin_skill_path("nonexistent_skill_xyz") is None


def test_is_builtin_skill():
    """is_builtin_skill returns True for imessage, False for unknown."""
    assert is_builtin_skill("imessage") is True
    assert is_builtin_skill("nonexistent_skill_xyz") is False


# --- Installation Tests ---


def test_install_builtin_skill_creates_directory(temp_cclaw_home):
    """install_builtin_skill creates the skill directory."""
    directory = install_builtin_skill("imessage")
    assert directory.exists()
    assert directory.is_dir()
    assert directory == temp_cclaw_home / "skills" / "imessage"


def test_install_builtin_skill_copies_files(temp_cclaw_home):
    """install_builtin_skill copies SKILL.md and skill.yaml."""
    directory = install_builtin_skill("imessage")
    assert (directory / "SKILL.md").exists()
    assert (directory / "skill.yaml").exists()

    # Verify content is actually copied (not empty)
    skill_md_content = (directory / "SKILL.md").read_text()
    assert "imsg" in skill_md_content

    with open(directory / "skill.yaml") as file:
        config = yaml.safe_load(file)
    assert config["name"] == "imessage"
    assert config["type"] == "cli"


def test_install_builtin_skill_already_exists(temp_cclaw_home):
    """install_builtin_skill raises FileExistsError when already installed."""
    install_builtin_skill("imessage")

    with pytest.raises(FileExistsError):
        install_builtin_skill("imessage")


def test_install_builtin_skill_unknown_name(temp_cclaw_home):
    """install_builtin_skill raises ValueError for unknown skill name."""
    with pytest.raises(ValueError):
        install_builtin_skill("nonexistent_skill_xyz")


def test_installed_skill_appears_in_list_skills(temp_cclaw_home):
    """Installed built-in skill shows up in list_skills()."""
    install_builtin_skill("imessage")

    skills = list_skills()
    names = [skill["name"] for skill in skills]
    assert "imessage" in names


def test_installed_skill_starts_inactive(temp_cclaw_home):
    """Installed built-in skill starts with inactive status."""
    install_builtin_skill("imessage")
    assert skill_status("imessage") == "inactive"


def test_installed_skill_is_recognized(temp_cclaw_home):
    """Installed built-in skill is recognized by is_skill()."""
    install_builtin_skill("imessage")
    assert is_skill("imessage") is True


def test_installed_skill_config_matches_template(temp_cclaw_home):
    """Installed skill config matches the template values."""
    install_builtin_skill("imessage")
    config = load_skill_config("imessage")
    assert config is not None
    assert config["name"] == "imessage"
    assert config["type"] == "cli"
    assert "imsg" in config["required_commands"]
    assert "allowed_tools" in config
    assert "Bash(imsg:*)" in config["allowed_tools"]


def test_installed_skill_requirements_check_with_missing_command(temp_cclaw_home):
    """check_skill_requirements reports missing commands with install hint."""
    install_builtin_skill("imessage")

    # Override required_commands to a command that definitely doesn't exist
    config = load_skill_config("imessage")
    config["required_commands"] = ["nonexistent_command_xyz"]
    config["install_hints"] = {"nonexistent_command_xyz": "Download from https://example.com"}

    save_skill_config("imessage", config)

    errors = check_skill_requirements("imessage")
    assert len(errors) == 1
    assert "nonexistent_command_xyz" in errors[0]
    assert "Install:" in errors[0]
    assert "https://example.com" in errors[0]


# --- Reminders Built-in Skill Tests ---


def test_list_builtin_skills_returns_reminders():
    """list_builtin_skills includes the reminders skill."""
    skills = list_builtin_skills()
    names = [skill["name"] for skill in skills]
    assert "reminders" in names

    reminders = next(skill for skill in skills if skill["name"] == "reminders")
    assert reminders["description"] != ""
    assert reminders["path"].is_dir()


def test_get_builtin_skill_path_reminders():
    """get_builtin_skill_path returns path for reminders skill."""
    path = get_builtin_skill_path("reminders")
    assert path is not None
    assert (path / "SKILL.md").exists()
    assert (path / "skill.yaml").exists()


def test_is_builtin_skill_reminders():
    """is_builtin_skill returns True for reminders."""
    assert is_builtin_skill("reminders") is True


def test_install_builtin_skill_reminders(temp_cclaw_home):
    """install_builtin_skill creates the reminders skill directory with files."""
    directory = install_builtin_skill("reminders")
    assert directory.exists()
    assert directory == temp_cclaw_home / "skills" / "reminders"
    assert (directory / "SKILL.md").exists()
    assert (directory / "skill.yaml").exists()

    # Verify SKILL.md content
    skill_md_content = (directory / "SKILL.md").read_text()
    assert "reminders" in skill_md_content

    # Verify skill.yaml content
    with open(directory / "skill.yaml") as file:
        config = yaml.safe_load(file)
    assert config["name"] == "reminders"
    assert config["type"] == "cli"
    assert "reminders" in config["required_commands"]
    assert "allowed_tools" in config
    assert "Bash(reminders:*)" in config["allowed_tools"]


def test_installed_reminders_skill_starts_inactive(temp_cclaw_home):
    """Installed reminders skill starts with inactive status."""
    install_builtin_skill("reminders")
    assert skill_status("reminders") == "inactive"
