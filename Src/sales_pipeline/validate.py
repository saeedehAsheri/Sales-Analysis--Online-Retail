
import pandas as pd

REQUIRED_COLUMNS = {
    "InvoiceNo",
    "StockCode",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
}


class DataValidationError(ValueError):
    """Raised when sales data has an invalid structure."""


def validate_columns(df: pd.DataFrame) -> None:
    """Check that all required columns exist in the dataset."""
    missing = REQUIRED_COLUMNS - set(df.columns)

    if missing:
        columns = ", ".join(sorted(missing))
        raise DataValidationError(
            f"Missing required columns: {columns}"
        )
