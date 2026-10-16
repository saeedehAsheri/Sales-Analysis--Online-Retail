
import pandas as pd
import pytest

from sales_pipeline.validate import (
    DataValidationError,
    validate_columns,
)


def test_valid_columns() -> None:
    """Accept a dataset containing all required columns."""
    df = pd.DataFrame(
        columns=[
            "InvoiceNo",
            "StockCode",
            "Quantity",
            "InvoiceDate",
            "UnitPrice",
        ]
    )

    validate_columns(df)


def test_missing_columns() -> None:
    """Reject a dataset with missing required columns."""
    df = pd.DataFrame(
        {"InvoiceNo": ["10001"]}
    )

    with pytest.raises(
        DataValidationError,
        match="Missing required columns",
    ):
        validate_columns(df)
