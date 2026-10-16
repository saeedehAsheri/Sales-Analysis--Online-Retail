
"""Identify source files using SHA-256 hashes."""

import hashlib
from pathlib import Path

CHUNK_SIZE = 1024 * 1024


class SourceFileError(Exception):
    """Raised when a source file cannot be processed."""


def calculate_file_hash(file_path: Path) -> str:
    """Calculate the SHA-256 hash of a source file."""
    path = Path(file_path)

    if not path.is_file():
        raise SourceFileError(
            f"Source file not found: {path}"
        )

    sha256 = hashlib.sha256()

    try:
        with path.open("rb") as file:
            while True:
                chunk = file.read(CHUNK_SIZE)

                if not chunk:
                    break

                sha256.update(chunk)

    except OSError as error:
        raise SourceFileError(
            f"Could not read source file: {path}"
        ) from error

    return sha256.hexdigest()


def create_source_identifier(
    file_hash: str,
    row_number: int,
) -> str:
    """Create a stable identifier for one source row."""
    if len(file_hash) != 64:
        raise ValueError("Invalid SHA-256 hash")

    if any(char not in "0123456789abcdef"
           for char in file_hash):
        raise ValueError("Invalid SHA-256 hash")

    if type(row_number) is not int or row_number < 2:
        raise ValueError("Invalid source row number")

    return f"{file_hash}:{row_number}"
