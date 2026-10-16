
"""End-to-end test from Excel to the analytical warehouse."""

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

TEST_DATABASE = "sales_analytics_test"


@pytest.fixture
def test_engine():
    """Provide an engine connected only to the test database."""
    original_engine = get_engine()

    try:
        url = original_engine.url.set(database=TEST_DATABASE)
    finally:
        original_engine.dispose()

    engine = create_engine(url)

    try:
        with engine.connect() as connection:
            database = connection.execute(
                text("SELECT current_database()")
            ).scalar_one()

        if database != TEST_DATABASE:
            raise RuntimeError("Unsafe test database connection")

        yield engine

    finally:
        engine.dispose()


def test_excel_to_warehouse(test_engine, tmp_path) -> None:
    """Verify loading, rejection tracking, and warehouse refresh."""
    file_path = tmp_path / "test_retail.xlsx"

    source_data = pd.DataFrame({
        "InvoiceNo": [
            "E2E-001",
            "CE2E-002",
            "E2E-003",
        ],
        "StockCode": [
            "E2E-PEN",
            "E2E-PEN",
            "E2E-INVALID",
        ],
        "Description": [
            "Test Pen",
            "Test Pen",
            "Invalid Product",
        ],
        "Quantity": [2, -1, 1],
        "InvoiceDate": pd.to_datetime([
            "2011-05-01",
            "2011-05-02",
            "2011-05-03",
        ]),
        "UnitPrice": [10.0, 10.0, 0.0],
        "CustomerID": [12345.0, 12345.0, 12345.0],
        "Country": ["Portugal"] * 3,
    })

    source_data.to_excel(file_path, index=False)

    raw_data = extract_sales_data(file_path)
    validate_columns(raw_data)

    result = transform_sales_data(raw_data)

    assert len(result.sales) == 1
    assert len(result.cancellations) == 1
    assert len(result.rejected) == 1

    file_hash = calculate_file_hash(file_path)

    with test_engine.connect() as connection:
        transaction = connection.begin()

        try:
            source_file_id = register_source_file(
                connection,
                file_hash,
                file_path.name,
            )

            inserted = load_transactions(
                result,
                connection,
                source_file_id,
            )

            rejected_inserted = load_rejected_records(
                result.rejected,
                connection,
                source_file_id,
            )

            assert inserted == 2
            assert rejected_inserted == 1

            refresh_warehouse(connection)

            retail_count = connection.execute(
                text("""
                    SELECT COUNT(*)
                    FROM retail.transactions
                    WHERE source_file_id = :file_id
                """),
                {"file_id": source_file_id},
            ).scalar_one()

            warehouse_count = connection.execute(
                text("""
                    SELECT COUNT(*)
                    FROM warehouse.fact_sales AS f
                    JOIN retail.transactions AS t
                        ON f.transaction_id = t.transaction_id
                    WHERE t.source_file_id = :file_id
                """),
                {"file_id": source_file_id},
            ).scalar_one()

            retail_total = connection.execute(
                text("""
                    SELECT SUM(total_price)
                    FROM retail.transactions
                    WHERE source_file_id = :file_id
                """),
                {"file_id": source_file_id},
            ).scalar_one()

            assert retail_count == 2
            assert warehouse_count == 2
            assert retail_total == 10

            # Repeated refreshes must not create duplicates.
            refresh_warehouse(connection)

            repeated_count = connection.execute(
                text("""
                    SELECT COUNT(*)
                    FROM warehouse.fact_sales AS f
                    JOIN retail.transactions AS t
                        ON f.transaction_id = t.transaction_id
                    WHERE t.source_file_id = :file_id
                """),
                {"file_id": source_file_id},
            ).scalar_one()

            assert repeated_count == 2

        finally:
            transaction.rollback()
