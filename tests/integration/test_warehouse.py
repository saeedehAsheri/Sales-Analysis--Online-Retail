
"""Read-only integration tests for the data warehouse."""

from decimal import Decimal

import pytest
from sqlalchemy import text

from sales_pipeline.db import get_engine


pytestmark = pytest.mark.integration


@pytest.fixture
def db_engine():
    """Provide a database engine for warehouse tests."""
    engine = get_engine()

    try:
        yield engine
    finally:
        engine.dispose()


def test_warehouse_row_count(db_engine) -> None:
    """Verify warehouse and retail have equal row counts."""
    query = text("""
        SELECT
            (SELECT COUNT(*) FROM retail.transactions)
                AS retail_count,
            (SELECT COUNT(*) FROM warehouse.fact_sales)
                AS warehouse_count
    """)

    with db_engine.connect() as connection:
        result = connection.execute(query).one()

    assert result.retail_count == result.warehouse_count


def test_warehouse_total_value(db_engine) -> None:
    """Verify warehouse preserves source transaction values."""
    query = text("""
        SELECT
            (SELECT COALESCE(SUM(total_price), 0)
             FROM retail.transactions) AS retail_total,
            (SELECT COALESCE(SUM(total_price), 0)
             FROM warehouse.fact_sales) AS warehouse_total
    """)

    with db_engine.connect() as connection:
        result = connection.execute(query).one()

    assert isinstance(result.retail_total, Decimal)
    assert result.retail_total == result.warehouse_total


def test_warehouse_no_missing_transactions(db_engine) -> None:
    """Verify every retail transaction exists in the warehouse."""
    query = text("""
        SELECT COUNT(*)
        FROM retail.transactions AS t
        WHERE NOT EXISTS (
            SELECT 1
            FROM warehouse.fact_sales AS f
            WHERE f.transaction_id = t.transaction_id
        )
    """)

    with db_engine.connect() as connection:
        missing = connection.execute(query).scalar_one()

    assert missing == 0


def test_warehouse_transaction_values_match(db_engine) -> None:
    """Verify each warehouse fact matches its source values."""
    query = text("""
        SELECT COUNT(*)
        FROM retail.transactions AS t
        JOIN warehouse.fact_sales AS f
            ON t.transaction_id = f.transaction_id
        WHERE t.quantity IS DISTINCT FROM f.quantity
           OR t.unit_price IS DISTINCT FROM f.unit_price
           OR t.total_price IS DISTINCT FROM f.total_price
           OR t.transaction_type
                IS DISTINCT FROM f.transaction_type
    """)

    with db_engine.connect() as connection:
        mismatches = connection.execute(query).scalar_one()

    assert mismatches == 0
