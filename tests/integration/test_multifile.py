
"""Integration tests for multi-file database loading."""

import hashlib

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

from sales_pipeline.db import get_engine
from sales_pipeline.load import (
    load_transactions,
    register_source_file,
)
from sales_pipeline.transform import TransformationResult

pytestmark = pytest.mark.integration

TEST_DATABASE = "sales_analytics_test"


@pytest.fixture
def test_engine():
    """Connect exclusively to the dedicated test database."""
    original_engine = get_engine()

    try:
        test_url = original_engine.url.set(
            database=TEST_DATABASE
        )
    finally:
        original_engine.dispose()

    engine = create_engine(test_url)

    try:
        with engine.connect() as connection:
            database_name = connection.execute(
                text("SELECT current_database()")
            ).scalar_one()

        if database_name != TEST_DATABASE:
            raise RuntimeError(
                "Refusing to test against a non-test database"
            )

        yield engine

    finally:
        engine.dispose()


def make_sales_result(
    invoice_no: str,
    stock_code: str,
) -> TransformationResult:
    """Create one valid sale at Excel row number two."""
    sales = pd.DataFrame({
        "InvoiceNo": [invoice_no],
        "StockCode": [stock_code],
        "Description": ["Test Product"],
        "Quantity": [2],
        "UnitPrice": [5.0],
        "TotalPrice": [10.0],
        "InvoiceDate": pd.to_datetime(["2011-06-01"]),
        "CustomerID": ["12345"],
        "Country": ["Portugal"],
    })

    sales.index = [0]

    return TransformationResult(
        sales=sales,
        cancellations=pd.DataFrame(),
        rejected=pd.DataFrame(),
    )


def test_two_files_with_same_row_number(test_engine) -> None:
    """Verify distinct files can contain identical row numbers."""
    first_hash = hashlib.sha256(
        b"integration-test-file-A"
    ).hexdigest()

    second_hash = hashlib.sha256(
        b"integration-test-file-B"
    ).hexdigest()

    result_a = make_sales_result("TEST-A", "NOTEBOOK")
    result_b = make_sales_result("TEST-B", "PEN")

    with test_engine.connect() as connection:
        transaction = connection.begin()

        try:
            file_a_id = register_source_file(
                connection,
                first_hash,
                "test_a.xlsx",
            )

            file_b_id = register_source_file(
                connection,
                second_hash,
                "test_b.xlsx",
            )

            assert file_a_id != file_b_id

            inserted_a = load_transactions(
                result_a,
                connection,
                file_a_id,
            )

            inserted_b = load_transactions(
                result_b,
                connection,
                file_b_id,
            )

            assert inserted_a == 1
            assert inserted_b == 1

            # Reloading the same file must not insert duplicates.
            inserted_again = load_transactions(
                result_a,
                connection,
                file_a_id,
            )

            assert inserted_again == 0

            rows = connection.execute(
                text("""
                    SELECT source_file_id, source_row_id
                    FROM retail.transactions
                    WHERE invoice_no IN ('TEST-A', 'TEST-B')
                    ORDER BY source_file_id
                """)
            ).fetchall()

            assert len(rows) == 2
            assert rows[0].source_row_id == 2
            assert rows[1].source_row_id == 2
            assert rows[0].source_file_id != rows[1].source_file_id

        finally:
            transaction.rollback()
