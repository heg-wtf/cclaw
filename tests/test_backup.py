"""Tests for cclaw.backup module."""

from pathlib import Path

import pytest
import pyzipper

from cclaw.backup import (
    EXCLUDE_DIRECTORY_NAMES,
    EXCLUDE_FILENAMES,
    collect_backup_files,
    create_encrypted_backup,
    generate_backup_filename,
)


@pytest.fixture
def temp_cclaw_home(tmp_path, monkeypatch):
    """Set CCLAW_HOME to a temporary directory with sample files."""
    home = tmp_path / ".cclaw"
    monkeypatch.setenv("CCLAW_HOME", str(home))

    # Create sample structure
    (home / "config.yaml").parent.mkdir(parents=True, exist_ok=True)
    (home / "config.yaml").write_text("bots: []\n")
    (home / "GLOBAL_MEMORY.md").write_text("# Global Memory\n")

    bot_directory = home / "bots" / "test-bot"
    bot_directory.mkdir(parents=True)
    (bot_directory / "bot.yaml").write_text("token: fake\n")
    (bot_directory / "CLAUDE.md").write_text("# test-bot\n")
    (bot_directory / "MEMORY.md").write_text("# Memory\n")

    skill_directory = home / "skills" / "test-skill"
    skill_directory.mkdir(parents=True)
    (skill_directory / "SKILL.md").write_text("# test-skill\n")

    return home


class TestGenerateBackupFilename:
    def test_format(self):
        """Filename matches YYMMDD-cclaw.zip format."""
        filename = generate_backup_filename()
        assert filename.endswith("-cclaw.zip")
        date_part = filename.split("-")[0]
        assert len(date_part) == 6
        assert date_part.isdigit()

    def test_contains_current_date(self):
        """Filename contains today's date."""
        from datetime import datetime

        today = datetime.now().strftime("%y%m%d")
        filename = generate_backup_filename()
        assert filename == f"{today}-cclaw.zip"


class TestCollectBackupFiles:
    def test_collects_all_files(self, temp_cclaw_home):
        """Collects all expected files from the home directory."""
        files = collect_backup_files(temp_cclaw_home)
        assert len(files) == 6
        names = {f.name for f in files}
        assert "config.yaml" in names
        assert "GLOBAL_MEMORY.md" in names
        assert "bot.yaml" in names
        assert "CLAUDE.md" in names
        assert "MEMORY.md" in names
        assert "SKILL.md" in names

    def test_excludes_pid_file(self, temp_cclaw_home):
        """cclaw.pid is excluded from backup."""
        (temp_cclaw_home / "cclaw.pid").write_text("12345")
        files = collect_backup_files(temp_cclaw_home)
        names = {f.name for f in files}
        assert "cclaw.pid" not in names

    def test_excludes_pycache(self, temp_cclaw_home):
        """__pycache__ directories are excluded."""
        pycache_directory = temp_cclaw_home / "bots" / "test-bot" / "__pycache__"
        pycache_directory.mkdir(parents=True)
        (pycache_directory / "module.cpython-312.pyc").write_bytes(b"\x00")
        files = collect_backup_files(temp_cclaw_home)
        names = {f.name for f in files}
        assert "module.cpython-312.pyc" not in names

    def test_returns_sorted(self, temp_cclaw_home):
        """Results are sorted by path."""
        files = collect_backup_files(temp_cclaw_home)
        assert files == sorted(files)

    def test_empty_directory(self, tmp_path):
        """Returns empty list for empty directory."""
        empty = tmp_path / "empty"
        empty.mkdir()
        files = collect_backup_files(empty)
        assert files == []

    def test_exclude_constants(self):
        """Verify exclusion constants are defined."""
        assert "cclaw.pid" in EXCLUDE_FILENAMES
        assert "__pycache__" in EXCLUDE_DIRECTORY_NAMES


class TestCreateEncryptedBackup:
    def test_creates_zip_file(self, temp_cclaw_home, tmp_path):
        """Creates a zip file at the specified output path."""
        output = tmp_path / "backup.zip"
        file_count = create_encrypted_backup(output, "test-password", temp_cclaw_home)
        assert output.exists()
        assert file_count == 6

    def test_correct_password_decrypts(self, temp_cclaw_home, tmp_path):
        """Zip contents can be read with the correct password."""
        output = tmp_path / "backup.zip"
        create_encrypted_backup(output, "correct-password", temp_cclaw_home)

        with pyzipper.AESZipFile(output, "r") as zip_file:
            zip_file.setpassword(b"correct-password")
            names = zip_file.namelist()
            assert "config.yaml" in names
            assert "GLOBAL_MEMORY.md" in names

            content = zip_file.read("config.yaml")
            assert content == b"bots: []\n"

    def test_wrong_password_fails(self, temp_cclaw_home, tmp_path):
        """Reading with wrong password raises an error."""
        output = tmp_path / "backup.zip"
        create_encrypted_backup(output, "correct-password", temp_cclaw_home)

        with pyzipper.AESZipFile(output, "r") as zip_file:
            zip_file.setpassword(b"wrong-password")
            with pytest.raises(RuntimeError):
                zip_file.read("config.yaml")

    def test_relative_paths_in_archive(self, temp_cclaw_home, tmp_path):
        """Archive uses relative paths from home directory."""
        output = tmp_path / "backup.zip"
        create_encrypted_backup(output, "password", temp_cclaw_home)

        with pyzipper.AESZipFile(output, "r") as zip_file:
            zip_file.setpassword(b"password")
            names = zip_file.namelist()
            for name in names:
                assert not Path(name).is_absolute()
            assert "bots/test-bot/bot.yaml" in names
            assert "skills/test-skill/SKILL.md" in names

    def test_excludes_pid_from_archive(self, temp_cclaw_home, tmp_path):
        """cclaw.pid is not included in the archive."""
        (temp_cclaw_home / "cclaw.pid").write_text("12345")
        output = tmp_path / "backup.zip"
        create_encrypted_backup(output, "password", temp_cclaw_home)

        with pyzipper.AESZipFile(output, "r") as zip_file:
            zip_file.setpassword(b"password")
            assert "cclaw.pid" not in zip_file.namelist()

    def test_empty_directory_creates_empty_zip(self, tmp_path):
        """Backing up an empty directory creates a valid zip with zero files."""
        empty_home = tmp_path / "empty"
        empty_home.mkdir()
        output = tmp_path / "backup.zip"
        file_count = create_encrypted_backup(output, "password", empty_home)
        assert file_count == 0
        assert output.exists()
