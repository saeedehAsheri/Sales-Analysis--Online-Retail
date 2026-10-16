
"""Tests for the extraction module."""

import pandas as pd
import pytest

from sales_pipeline.extract import (
    DataExtractionError,
    extract_sales_data,
)


def test_extract_valid_excel(tmp_path) -> None:
    """Verify that an Excel file is loaded correctly."""
    file_path = tmp_path / "test_sales.xlsx"


    expected = pd.DataFrame({
        "InvoiceNo": pd.Series(
        ["1001", "1002"],
        dtype=pd.StringDtype(
            storage="python",
            na_value=pd.NA,
        ),
    ),
    "Quantity": [2, 5],
    "UnitPrice": [10.0, 20.0],
    })


    expected.to_excel(file_path, index=False)

    actual = extract_sales_data(file_path)

    pd.testing.assert_frame_equal(actual, expected)


def test_extract_missing_file(tmp_path) -> None:
    """Verify that a missing file raises an error."""
    file_path = tmp_path / "missing.xlsx"

    with pytest.raises(
        DataExtractionError,
        match="Dataset not found",
    ):
        extract_sales_data(file_path)


def test_extract_empty_excel(tmp_path) -> None:
    """Verify that an empty dataset is rejected."""
    file_path = tmp_path / "empty.xlsx"

    pd.DataFrame().to_excel(file_path, index=False)

    with pytest.raises(
        DataExtractionError,
        match="contains no records",
    ):
        extract_sales_data(file_path)

def test_invoice_preserves_leading_zeros(tmp_path) -> None:
    """Verify invoice identifiers preserve leading zeros."""
    file_path = tmp_path / "invoice_codes.xlsx"

    expected = pd.DataFrame({
        "InvoiceNo": ["001001", "001002"],
        "StockCode": ["A01", "B02"],
        "Quantity": [2, 3],
    })

    expected.to_excel(file_path, index=False)

    actual = extract_sales_data(file_path)

    assert actual["InvoiceNo"].tolist() == [
        "001001",
        "001002",
    ]
