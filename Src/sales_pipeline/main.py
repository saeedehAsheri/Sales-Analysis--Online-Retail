
"""Main entry point for the retail sales pipeline."""

import logging
from pathlib import Path
from sales_pipeline.warehouse import refresh_warehouse

from sales_pipeline.config import RAW_DATA_PATH, setup_logging
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

logger = logging.getLogger(__name__)


def run_pipeline(file_path: Path) -> None:
    """Process a source file in one atomic database transaction."""
    file_path = Path(file_path)

    logger.info("Processing source file: %s", file_path)

    file_hash = calculate_file_hash(file_path)

    raw_data = extract_sales_data(file_path)
    validate_columns(raw_data)

    result = transform_sales_data(raw_data)

    total_rows = (
        len(result.sales)
        + len(result.cancellations)
        + len(result.rejected)
    )

    if total_rows != len(raw_data):
        raise ValueError(
            "Row count mismatch after transformation"
        )

    logger.info("Valid sales: %d", len(result.sales))
    logger.info(
        "Cancellations: %d",
        len(result.cancellations),
    )
    logger.info(
        "Rejected records: %d",
        len(result.rejected),
    )

    engine = get_engine()

    try:
        with engine.begin() as connection:
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
            refresh_warehouse(connection)

        logger.info(
            "New transactions inserted: %d",
            inserted,
        )
        logger.info(
            "New rejected records inserted: %d",
            rejected_inserted,
        )
        logger.info("Atomic database load committed")

    finally:
        engine.dispose()


def main() -> int:
    """Run the retail ETL pipeline."""
    setup_logging()

    try:
        logger.info("Starting Sales Analysis Pipeline")

        run_pipeline(RAW_DATA_PATH)

        logger.info("Pipeline completed successfully")
        return 0

    except Exception:
        logger.exception("Pipeline failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
