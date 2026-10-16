
"""Extract raw retail transactions from an Excel file."""

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


class DataExtractionError(Exception):
    """Raised when a dataset cannot be extracted."""


def extract_sales_data(file_path: Path) -> pd.DataFrame:
    """Read sales transactions without modifying the raw data."""
    path = Path(file_path)

    if not path.is_file():
        raise DataExtractionError(
            f"Dataset not found: {path}"
        )

    logger.info("Starting extraction from %s", path)

    try:

        dataframe = pd.read_excel(
        path,
        engine="openpyxl",
        dtype={
        "InvoiceNo": pd.StringDtype(
            storage="python",
            na_value=pd.NA,
        ),
        "StockCode": pd.StringDtype(
            storage="python",
            na_value=pd.NA,
        ),
        "UnitPrice": "float64",
        },
        )


    except (OSError, ValueError, ImportError, Exception) as error:
        logger.exception("Failed to read dataset")
        raise DataExtractionError(
            f"Could not read dataset: {path}"
        ) from error

    if dataframe.empty:
        raise DataExtractionError(
            "The dataset contains no records."
        )

    logger.info(
        "Extraction completed: %d rows, %d columns",
        len(dataframe),
        len(dataframe.columns),
    )

    return dataframe
