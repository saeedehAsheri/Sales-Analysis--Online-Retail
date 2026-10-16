
"""Backfill source file IDs for existing retail records."""

import logging

from sqlalchemy import text

from sales_pipeline.config import (
    RAW_DATA_PATH,
    setup_logging,
)
from sales_pipeline.db import get_engine
from sales_pipeline.source import calculate_file_hash

logger = logging.getLogger(__name__)


def backfill_source_file() -> None:
    """Link legacy database records to the original Excel file."""
    file_hash = calculate_file_hash(RAW_DATA_PATH)
    file_name = RAW_DATA_PATH.name

    engine = get_engine()

    try:
        with engine.begin() as connection:
            source_file_id = connection.execute(
                text("""
                    INSERT INTO retail.source_files (
                        file_hash,
                        file_name
                    )
                    VALUES (
                        :file_hash,
                        :file_name
                    )
                    ON CONFLICT (file_hash)
                    DO UPDATE SET
                        file_name = EXCLUDED.file_name
                    RETURNING source_file_id
                """),
                {
                    "file_hash": file_hash,
                    "file_name": file_name,
                },
            ).scalar_one()

            logger.info(
                "Registered source file ID: %s",
                source_file_id,
            )

            for table_name in (
                "transactions",
                "rejected_transactions",
            ):
                conflict_count = connection.execute(
                    text(f"""
                        SELECT COUNT(*)
                        FROM retail.{table_name}
                        WHERE source_file_id IS NOT NULL
                          AND source_file_id != :source_file_id
                    """),
                    {"source_file_id": source_file_id},
                ).scalar_one()

                if conflict_count:
                    raise ValueError(
                        f"{table_name} contains "
                        f"{conflict_count} records linked "
                        "to a different source file"
                    )

                response = connection.execute(
                    text(f"""
                        UPDATE retail.{table_name}
                        SET source_file_id = :source_file_id
                        WHERE source_file_id IS NULL
                    """),
                    {"source_file_id": source_file_id},
                )

                logger.info(
                    "Backfilled %s rows: %d",
                    table_name,
                    response.rowcount,
                )

        logger.info("Backfill committed successfully")

    finally:
        engine.dispose()


def main() -> int:
    """Run the legacy source file backfill."""
    setup_logging()

    try:
        backfill_source_file()
        return 0

    except Exception:
        logger.exception("Source file backfill failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
