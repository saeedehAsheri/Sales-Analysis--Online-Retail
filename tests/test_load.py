
"""Tests for database record preparation."""

import pandas as pd

from sales_pipeline.load import prepare_records


def test_prepare_sales_records() -> None:
    """Verify sales are converted to source-aware records."""
    df = pd.DataFrame({
        "InvoiceNo": ["1001"],
        "StockCode": ["A01"],
        "Description": ["Notebook"],
        "Quantity": [2],
        "UnitPrice": [10.50],
        "TotalPrice": [21.00],
        "InvoiceDate": pd.to_datetime(["2026-01-01"]),
        "CustomerID": ["123"],
        "Country": ["Portugal"],
    })

    source_file_id = 1

    records = prepare_records(
        df,
        "SALE",
        source_file_id,
    )

    assert len(records) == 1

    record = records[0]

    assert record["source_file_id"] == 1
    assert record["source_row_id"] == 2
    assert record["invoice_no"] == "1001"
    assert record["stock_code"] == "A01"
    assert record["quantity"] == 2
    assert record["unit_price"] == 10.50
    assert record["total_price"] == 21.00
    assert record["customer_id"] == "123"
    assert record["transaction_type"] == "SALE"


def test_customer_id_without_decimal_suffix() -> None:
    """Verify numeric customer IDs have no .0 suffix."""
    df = pd.DataFrame({
        "InvoiceNo": ["1002"],
        "StockCode": ["A02"],
        "Description": ["Pen"],
        "Quantity": [1],
        "UnitPrice": [2.50],
        "TotalPrice": [2.50],
        "InvoiceDate": pd.to_datetime(["2026-01-01"]),
        "CustomerID": [13952.0],
        "Country": ["Portugal"],
    })

    records = prepare_records(
        df,
        "SALE",
        source_file_id=1,
    )

    assert records[0]["customer_id"] == "13952"


def test_monetary_values_use_decimal() -> None:
    """Verify monetary records use Decimal values."""
    from decimal import Decimal

    df = pd.DataFrame({
        "InvoiceNo": ["1003"],
        "StockCode": ["PADS"],
        "Description": ["Small Price Item"],
        "Quantity": [3],
        "UnitPrice": [0.001],
        "TotalPrice": [0.003],
        "InvoiceDate": pd.to_datetime(["2026-01-01"]),
        "CustomerID": ["12345"],
        "Country": ["Portugal"],
    })

    records = prepare_records(
        df,
        "SALE",
        source_file_id=1,
    )

    record = records[0]

    assert isinstance(record["unit_price"], Decimal)
    assert isinstance(record["total_price"], Decimal)

    assert record["unit_price"] == Decimal("0.001")
    assert record["total_price"] == Decimal("0.003")
