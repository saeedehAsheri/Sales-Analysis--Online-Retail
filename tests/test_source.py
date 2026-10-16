
"""Tests for source file identification."""

import hashlib

import pytest

from sales_pipeline.source import (
    SourceFileError,
    calculate_file_hash,
    create_source_identifier,
)


def test_file_hash_is_deterministic(tmp_path) -> None:
    """Verify identical file content produces the same hash."""
    path = tmp_path / "sales.csv"
    path.write_text("invoice,quantity\n1001,2\n")

    first_hash = calculate_file_hash(path)
    second_hash = calculate_file_hash(path)

    assert first_hash == second_hash
    assert len(first_hash) == 64


def test_different_content_changes_hash(tmp_path) -> None:
    """Verify different contents produce different hashes."""
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"

    first.write_text("1001,2")
    second.write_text("1001,3")

    assert calculate_file_hash(first) != calculate_file_hash(
        second
    )


def test_same_content_same_hash(tmp_path) -> None:
    """Verify filenames do not change a content hash."""
    first = tmp_path / "a.csv"
    second = tmp_path / "b.csv"

    first.write_bytes(b"same content")
    second.write_bytes(b"same content")

    assert calculate_file_hash(first) == calculate_file_hash(
        second
    )


def test_missing_source_file(tmp_path) -> None:
    """Reject a missing source file."""
    with pytest.raises(
        SourceFileError,
        match="Source file not found",
    ):
        calculate_file_hash(tmp_path / "missing.xlsx")


def test_source_identifier() -> None:
    """Verify that file hash and row create a stable ID."""
    file_hash = hashlib.sha256(b"data").hexdigest()

    identifier = create_source_identifier(file_hash, 5)

    assert identifier == f"{file_hash}:5"


def test_invalid_row_number() -> None:
    """Reject an invalid Excel row number."""
    file_hash = hashlib.sha256(b"data").hexdigest()

    with pytest.raises(ValueError):
        create_source_identifier(file_hash, 0)
