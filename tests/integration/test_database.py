
"""Integration tests for PostgreSQL."""

from decimal import Decimal

import pandas as pd
import pytest
from sqlalchemy import text

from sales_pipeline.db import get_engine
from sales_pipeline.load import (
    load_rejected_records,
    load_transactions,
    register_source_file,
)
from sales_pipeline.transform import TransformationResult

pytestmark = pytest.mark.integration


@pytest.fixture
def db_engine():
    """Create and clean up a database engine."""
    engine = get_engine()

    try:
        yield engine
    finally:
        engine.dispose()


def test_database_connection(db_engine) -> None:
    """Check that PostgreSQL accepts connections."""
    with db_engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))

    assert result.scalar_one() == 1


def test_transactions_exist(db_engine) -> None:
    """Check that sales transactions exist."""
    query = text(
        "SELECT COUNT(*) FROM retail.transactions"
    )

    with db_engine.connect() as connection:
        count = connection.execute(query).scalar_one()

    assert count > 0


def test_small_price_precision(db_engine) -> None:
    """Check that small prices are stored correctly."""
    query = text("""
        SELECT unit_price
        FROM retail.transactions
        WHERE invoice_no = '550193'
          AND stock_code = 'PADS'
    """)

    with db_engine.connect() as connection:
        price = connection.execute(query).scalar_one()

    assert price == Decimal("0.0010")




def test_no_duplicate_source_rows(db_engine) -> None:
    """Verify source file and row combinations are unique."""
    query = text("""
        SELECT
            COUNT(*) -
            COUNT(DISTINCT (source_file_id, source_row_id))
        FROM retail.transactions
    """)

    with db_engine.connect() as connection:
        duplicates = connection.execute(
            query
        ).scalar_one()

    assert duplicates == 0




def test_atomic_load_rollback(db_engine) -> None:
    """Verify failed transactions roll back all inserted records."""
    import hashlib

    sale_id = -900000001
    rejected_id = -900000002

    file_hash = hashlib.sha256(
        b"atomic-rollback-integration-test"
    ).hexdigest()

    sales = pd.DataFrame({
        "InvoiceNo": ["TEST-ROLLBACK"],
        "StockCode": ["TEST01"],
        "Description": ["Test Product"],
        "Quantity": [2],
        "UnitPrice": [10.0],
        "TotalPrice": [20.0],
        "InvoiceDate": pd.to_datetime(["2011-01-01"]),
        "CustomerID": ["123"],
        "Country": ["Portugal"],
    })
    sales.index = [sale_id - 2]

    rejected = pd.DataFrame({
        "InvoiceNo": ["TEST-REJECTED"],
        "StockCode": ["TEST02"],
        "Description": ["Invalid Test Product"],
        "Quantity": [1],
        "UnitPrice": [0.0],
        "InvoiceDate": pd.to_datetime(["2011-01-01"]),
        "CustomerID": ["123"],
        "Country": ["Portugal"],
    })
    rejected.index = [rejected_id - 2]

    result = TransformationResult(
        sales=sales,
        cancellations=pd.DataFrame(),
        rejected=rejected,
    )

    with db_engine.connect() as connection:
        for table_name, row_id in [
            ("transactions", sale_id),
            ("rejected_transactions", rejected_id),
        ]:
            count = connection.execute(
                text(
                    f"SELECT COUNT(*) FROM retail.{table_name} "
                    "WHERE source_row_id = :row_id"
                ),
                {"row_id": row_id},
            ).scalar_one()

            assert count == 0

    with pytest.raises(
        RuntimeError,
        match="Simulated failure",
    ), db_engine.begin() as connection:
        source_file_id = register_source_file(
            connection,
            file_hash,
            "rollback_test.xlsx",
        )

        assert load_transactions(
            result,
            connection,
            source_file_id,
        ) == 1

        assert load_rejected_records(
            rejected,
            connection,
            source_file_id,
        ) == 1

        raise RuntimeError("Simulated failure")

    with db_engine.connect() as connection:
        sales_count = connection.execute(
            text(
                "SELECT COUNT(*) FROM retail.transactions "
                "WHERE source_row_id = :row_id"
            ),
            {"row_id": sale_id},
        ).scalar_one()

        rejected_count = connection.execute(
            text(
                "SELECT COUNT(*) "
                "FROM retail.rejected_transactions "
                "WHERE source_row_id = :row_id"
            ),
            {"row_id": rejected_id},
        ).scalar_one()

        file_count = connection.execute(
            text(
                "SELECT COUNT(*) FROM retail.source_files "
                "WHERE file_hash = :file_hash"
            ),
            {"file_hash": file_hash},
        ).scalar_one()

    assert sales_count == 0
    assert rejected_count == 0
    assert file_count == 0


def test_customer_ids_are_normalized(db_engine) -> None:
    """Verify legacy decimal-suffixed customer IDs are gone."""
    query = text("""
        SELECT COUNT(*)
        FROM retail.transactions
        WHERE customer_id ~ '^[0-9]+[.]0$'
    """)

    with db_engine.connect() as connection:
        count = connection.execute(query).scalar_one()

    assert count == 0
