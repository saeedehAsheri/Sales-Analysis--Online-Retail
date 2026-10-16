
"""Database connection management."""

import logging

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from sales_pipeline.config import get_database_url

logger = logging.getLogger(__name__)


def get_engine() -> Engine:
    """Create a reusable SQLAlchemy database engine."""
    return create_engine(
        get_database_url(),
        pool_pre_ping=True,
        pool_size=5,
    )


def check_database_connection(engine: Engine) -> bool:
    """Verify that PostgreSQL accepts SQL queries."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            success = result.scalar_one() == 1

        if success:
            logger.info("Database connection successful")

        return success

    except Exception:
        logger.exception("Database connection failed")
        return False


def main() -> int:
    """Test PostgreSQL connectivity."""
    logging.basicConfig(level=logging.INFO)
    engine = None

    try:
        engine = get_engine()
        return 0 if check_database_connection(engine) else 1

    except Exception:
        logger.exception("Could not initialize database")
        return 1

    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
