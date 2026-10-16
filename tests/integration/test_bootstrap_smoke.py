
"""Smoke test for a freshly bootstrapped database."""

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

from sales_pipeline.db import get_engine
from sales_pipeline.extract import extract_sales_data
from sales_pipeline.load import (
    load_rejected_records,
    load_transactions,
    register_source_file,
)
from sales_pipeline.source import calculate_file_hash
from sales_pipeline.transform import transform_sales_data
from sales_pipeline.validate import validate_columns
from sales_pipeline.warehouse import refresh_warehouse


pytestmark = pytest.mark.integration

TEST_DATABASE = "sales_bootstrap_check"


def test_bootstrap_pipeline(tmp_path) -> None:
    """Verify ETL and warehouse loading on a fresh database."""
    file_path = tmp_path / "bootstrap_test.xlsx"

    data = pd.DataFrame({
        "InvoiceNo": ["BOOT-001", "CBOOT-002", "BOOT-003"],
        "StockCode": ["PEN", "PEN", "INVALID"],
        "Description": ["Pen", "Pen", "Invalid"],
        "Quantity": [2, -1, 1],
        "InvoiceDate": pd.to_datetime([
            "2011-06-01",
            "2011-06-02",
            "2011-06-03",
        ]),
        "UnitPrice": [5.0, 5.0, 0.0],
        "CustomerID": [12345.0, 12345.0, 12345.0],
        "Country": ["Portugal"] * 3,
    })

    data.to_excel(file_path, index=False)

    raw_data = extract_sales_data(file_path)
    validate_columns(raw_data)
    result = transform_sales_data(raw_data)

    assert len(result.sales) == 1
    assert len(result.cancellations) == 1
    assert len(result.rejected) == 1

    original_engine = get_engine()

    try:
        test_url = original_engine.url.set(
            database=TEST_DATABASE
        )
    finally:
        original_engine.dispose()

    engine = create_engine(test_url)

    try:
        with engine.begin() as connection:
            current_db = connection.execute(
                text("SELECT current_database()")
            ).scalar_one()

            if current_db != TEST_DATABASE:
                raise RuntimeError(
                    "Refusing to use a non-test database"
                )

            file_id = register_source_file(
                connection,
                calculate_file_hash(file_path),
                file_path.name,
            )

            assert load_transactions(
                result,
                connection,
                file_id,
            ) == 2

            assert load_rejected_records(
                result.rejected,
                connection,
                file_id,
            ) == 1

            refresh_warehouse(connection)

            retail_count = connection.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM retail.transactions"
                )
            ).scalar_one()

            fact_count = connection.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM warehouse.fact_sales"
                )
            ).scalar_one()

            assert retail_count == 2
            assert fact_count == 2

            # Force rollback to leave the test database empty.
            raise RuntimeError("Rollback smoke test data")

    except RuntimeError as error:
        if str(error) != "Rollback smoke test data":
            raise

    finally:
        engine.dispose()
