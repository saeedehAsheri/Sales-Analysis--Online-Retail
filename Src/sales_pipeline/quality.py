
"""Data quality checks for retail transactions."""

import json

import pandas as pd


def get_rejection_reasons(row: pd.Series) -> list[str]:
    """Return all quality violations for a transaction."""
    reasons = []

    invoice = row.get("InvoiceNo")
    stock_code = row.get("StockCode")
    quantity = pd.to_numeric(
        row.get("Quantity"), errors="coerce"
    )
    price = pd.to_numeric(
        row.get("UnitPrice"), errors="coerce"
    )
    date = pd.to_datetime(
        row.get("InvoiceDate"), errors="coerce"
    )

    if pd.isna(invoice) or not str(invoice).strip():
        reasons.append("MISSING_INVOICE")

    if pd.isna(stock_code) or not str(stock_code).strip():
        reasons.append("MISSING_STOCK_CODE")

    if pd.isna(date):
        reasons.append("INVALID_DATE")

    if pd.isna(quantity) or quantity == 0 or quantity != int(quantity):
        reasons.append("INVALID_QUANTITY")

    if pd.isna(price) or price <= 0:
        reasons.append("INVALID_PRICE")

    if not pd.isna(invoice) and not pd.isna(quantity):
        is_cancelled = str(invoice).startswith("C")

        if is_cancelled and quantity > 0:
            reasons.append(
                "INVALID_CANCELLATION_QUANTITY"
            )
        elif not is_cancelled and quantity < 0:
            reasons.append("INVALID_SALE_QUANTITY")

    return reasons


def prepare_rejected_records(
    rejected: pd.DataFrame,
) -> list[dict]:
    """Prepare rejected rows for PostgreSQL storage."""
    records = []

    for index, row in rejected.iterrows():
        reasons = get_rejection_reasons(row)

        records.append({
            "source_row_id": int(index) + 2,
            "rejection_reasons": reasons,
            "raw_data": json.loads(
                row.to_json(date_format="iso")
            ),
        })

    return records
