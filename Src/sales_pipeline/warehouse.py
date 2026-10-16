
"""Refresh analytical warehouse tables."""

import logging

from sqlalchemy import text
from sqlalchemy.engine import Connection

from sales_pipeline.config import PROJECT_ROOT


logger = logging.getLogger(__name__)


WAREHOUSE_QUERIES = (
    "01_products.sql",
    "02_customers.sql",
    "03_countries.sql",
    "04_dates.sql",
    "05_facts.sql",
)


def refresh_warehouse(connection: Connection) -> None:
    """Refresh warehouse tables inside an existing transaction."""
    sql_dir = PROJECT_ROOT / "sql" / "warehouse"

    for file_name in WAREHOUSE_QUERIES:
        sql_path = sql_dir / file_name

        query = sql_path.read_text(encoding="utf-8")

        logger.info("Executing warehouse query: %s", file_name)

        connection.execute(text(query))

    logger.info("Warehouse refresh statements completed")
