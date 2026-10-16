"""Tests for sales data transformation."""

from decimal import Decimal

import pandas as pd

from sales_pipeline.transform import (
    calculate_total_price,
    transform_sales_data,
)
def create_sample_data() -> pd.DataFrame:
    """Create a small retail dataset for testing."""
    return pd.DataFrame({
        "InvoiceNo": ["1001", "C1002", "1003", "1004"],
        "StockCode": ["A01", "B02", "C03", "D04"],
        "Quantity": [2, -1, 0, 3],
        "UnitPrice": [10.0, 20.0, 15.0, -5.0],
        "InvoiceDate": ["2026-01-01"] * 4,
    })


def test_valid_sales() -> None:
    """Verify that valid sales are retained."""
    result = transform_sales_data(create_sample_data())

    assert len(result.sales) == 1
    assert result.sales.iloc[0]["InvoiceNo"] == "1001"


def test_cancellations() -> None:
    """Verify that cancelled transactions are separated."""
    result = transform_sales_data(create_sample_data())

    assert len(result.cancellations) == 1
    assert result.cancellations.iloc[0]["InvoiceNo"] == "C1002"


def test_rejected_rows() -> None:
    """Verify that invalid transactions are rejected."""
    result = transform_sales_data(create_sample_data())

    assert len(result.rejected) == 2


def test_total_price() -> None:
    """Verify that sales revenue is calculated correctly."""
    result = transform_sales_data(create_sample_data())

    assert result.sales.iloc[0]["TotalPrice"] == 20.0
    assert result.cancellations.iloc[0]["TotalPrice"] == -20.0


def test_input_unchanged() -> None:
    """Verify that transformation does not modify input."""
    original = create_sample_data()
    snapshot = original.copy(deep=True)

    transform_sales_data(original)

    pd.testing.assert_frame_equal(original, snapshot)


def test_no_rows_lost() -> None:
    """Verify that every input row is accounted for."""
    original = create_sample_data()
    result = transform_sales_data(original)

    total = (
        len(result.sales)
        + len(result.cancellations)
        + len(result.rejected)
    )

    assert total == len(original)



def test_decimal_total_price() -> None:
    """Verify exact decimal multiplication."""
    result = calculate_total_price(3, 0.1)

    assert result == Decimal("0.3000")
    assert isinstance(result, Decimal)


def test_small_decimal_price() -> None:
    """Verify small unit prices are preserved."""
    result = calculate_total_price(3, 0.001)

    assert result == Decimal("0.0030")


def test_negative_total_price() -> None:
    """Verify cancellation totals remain negative."""
    result = calculate_total_price(-2, 10.50)

    assert result == Decimal("-21.0000")


def test_decimal_rounding() -> None:
    """Verify the configured four-decimal precision."""
    result = calculate_total_price(3, Decimal("0.00005"))

    assert result == Decimal("0.0002")
