
"""Tests for rejected transaction quality checks."""

import pandas as pd

from sales_pipeline.quality import (
    get_rejection_reasons,
    prepare_rejected_records,
)


def make_row(
    invoice: str = "1001",
    quantity: int = 2,
    price: float = 10.0,
) -> pd.Series:
    """Create a sample transaction."""
    return pd.Series({
        "InvoiceNo": invoice,
        "StockCode": "A01",
        "Quantity": quantity,
        "UnitPrice": price,
        "InvoiceDate": "2011-01-01",
    })


def test_valid_row_has_no_reasons() -> None:
    """Confirm valid transactions have no quality errors."""
    assert get_rejection_reasons(make_row()) == []


def test_zero_price() -> None:
    """Reject a transaction with a zero price."""
    row = make_row(price=0.0)

    assert "INVALID_PRICE" in get_rejection_reasons(row)


def test_invalid_sale_quantity() -> None:
    """Reject negative quantities on normal sales."""
    row = make_row(quantity=-2)

    assert (
        "INVALID_SALE_QUANTITY"
        in get_rejection_reasons(row)
    )


def test_multiple_rejection_reasons() -> None:
    """Collect multiple problems in the same record."""
    row = make_row(quantity=0, price=-5.0)
    reasons = get_rejection_reasons(row)

    assert "INVALID_QUANTITY" in reasons
    assert "INVALID_PRICE" in reasons


def test_prepare_rejected_records() -> None:
    """Preserve source identity and rejection reasons."""
    df = pd.DataFrame([make_row(price=0.0)])

    records = prepare_rejected_records(df)

    assert len(records) == 1
    assert records[0]["source_row_id"] == 2
    assert records[0]["rejection_reasons"] == [
        "INVALID_PRICE"
    ]
    assert records[0]["raw_data"]["UnitPrice"] == 0.0
