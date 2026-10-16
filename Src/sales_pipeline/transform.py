
"""Clean and transform retail transaction data."""

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal

import pandas as pd

MONEY_PRECISION = Decimal("0.0001")


@dataclass
class TransformationResult:
    """Store the results of transforming sales data."""

    sales: pd.DataFrame
    cancellations: pd.DataFrame
    rejected: pd.DataFrame


def calculate_total_price(
    quantity: float,
    unit_price: float | Decimal,
) -> Decimal:
    """Calculate a transaction total using Decimal arithmetic."""
    quantity_decimal = Decimal(str(quantity))
    price_decimal = Decimal(str(unit_price))

    total = quantity_decimal * price_decimal

    return total.quantize(
        MONEY_PRECISION,
        rounding=ROUND_HALF_EVEN,
    )


def transform_sales_data(
    df: pd.DataFrame,
) -> TransformationResult:
    """Separate valid sales, cancellations, and invalid rows."""
    data = df.copy()

    data["InvoiceNo"] = data["InvoiceNo"].astype("string")
    data["StockCode"] = data["StockCode"].astype("string")

    data["Quantity"] = pd.to_numeric(
        data["Quantity"], errors="coerce"
    )
    data["UnitPrice"] = pd.to_numeric(
        data["UnitPrice"], errors="coerce"
    )
    data["InvoiceDate"] = pd.to_datetime(
        data["InvoiceDate"], errors="coerce"
    )

    invoice = data["InvoiceNo"]
    cancelled = invoice.str.startswith(
        "C", na=False
    ).fillna(False)

    invalid = (
        data["InvoiceNo"].isna()
        | data["StockCode"].isna()
        | data["InvoiceDate"].isna()
        | data["Quantity"].isna()
        | data["UnitPrice"].isna()
        | (data["Quantity"] == 0)
        | (data["UnitPrice"] <= 0)
    )

    sales_mask = (
        ~invalid
        & ~cancelled
        & (data["Quantity"] > 0)
    )

    cancellation_mask = (
        ~invalid
        & cancelled
        & (data["Quantity"] < 0)
    )

    rejected_mask = ~(sales_mask | cancellation_mask)

    sales = data.loc[sales_mask].copy()
    cancellations = data.loc[cancellation_mask].copy()
    rejected = data.loc[rejected_mask].copy()

    sales["TotalPrice"] = [
        calculate_total_price(qty, price)
        for qty, price in zip(
            sales["Quantity"],
            sales["UnitPrice"],
        )
    ]

    cancellations["TotalPrice"] = [
        calculate_total_price(qty, price)
        for qty, price in zip(
            cancellations["Quantity"],
            cancellations["UnitPrice"],
        )
    ]

    return TransformationResult(
        sales=sales,
        cancellations=cancellations,
        rejected=rejected,
    )
