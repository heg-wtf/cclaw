"""Backup cclaw home directory to an encrypted zip file."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pyzipper

EXCLUDE_FILENAMES = {"cclaw.pid"}
EXCLUDE_DIRECTORY_NAMES = {"__pycache__"}


def generate_backup_filename() -> str:
    """Generate a backup filename in YYMMDD-cclaw.zip format."""
    return datetime.now().strftime("%y%m%d") + "-cclaw.zip"


def collect_backup_files(home_directory: Path) -> list[Path]:
    """Collect all files to back up, excluding runtime artifacts.

    Excludes:
        - cclaw.pid (runtime PID file)
        - __pycache__/ directories

    Returns:
        Sorted list of file paths.
    """
    files: list[Path] = []
    for path in home_directory.rglob("*"):
        if not path.is_file():
            continue
        if path.name in EXCLUDE_FILENAMES:
            continue
        if any(part in EXCLUDE_DIRECTORY_NAMES for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def create_encrypted_backup(
    output_path: Path,
    password: str,
    home_directory: Path,
) -> int:
    """Create an AES-256 encrypted zip backup of the cclaw home directory.

    Args:
        output_path: Path where the zip file will be written.
        password: Encryption password.
        home_directory: The cclaw home directory to back up.

    Returns:
        Number of files included in the backup.
    """
    files = collect_backup_files(home_directory)

    with pyzipper.AESZipFile(
        output_path,
        "w",
        compression=pyzipper.ZIP_DEFLATED,
        encryption=pyzipper.WZ_AES,
    ) as zip_file:
        zip_file.setpassword(password.encode())
        for file_path in files:
            archive_name = file_path.relative_to(home_directory)
            zip_file.write(file_path, arcname=str(archive_name))

    return len(files)
