
"""Integration tests for automated warehouse refresh."""

import pytest
from sqlalchemy import create_engine, text

from sales_pipeline.db import get_engine
from sales_pipeline.warehouse import refresh_warehouse


pytestmark = pytest.mark.integration

TEST_DATABASE = "sales_analytics_test"


@pytest.fixture
def test_engine():
    """Create an engine for the isolated test database."""
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

        assert database_name == TEST_DATABASE

        yield engine

    finally:
        engine.dispose()


def test_warehouse_refresh_is_idempotent(test_engine) -> None:
    """Verify repeated refreshes do not duplicate facts."""
    with test_engine.connect() as connection:
        transaction = connection.begin()

        try:
            refresh_warehouse(connection)

            first_count = connection.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM warehouse.fact_sales"
                )
            ).scalar_one()

            refresh_warehouse(connection)

            second_count = connection.execute(
                text(
                    "SELECT COUNT(*) "
                    "FROM warehouse.fact_sales"
                )
            ).scalar_one()

            assert first_count == second_count

        finally:
            transaction.rollback()
