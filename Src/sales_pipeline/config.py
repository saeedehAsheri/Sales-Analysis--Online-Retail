
"""Project configuration and logging setup."""

import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DATA_PATH = (
    PROJECT_ROOT / "data" / "raw" / "Online Retail.xlsx"
)


def setup_logging() -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
        force=True,
    )

"""Additional database configuration."""

import os

from dotenv import load_dotenv
from sqlalchemy import URL

load_dotenv()


def get_database_url() -> URL:
    """Build a PostgreSQL URL from environment settings."""
    required = [
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
    ]

    missing = [key for key in required if not os.getenv(key)]

    if missing:
        raise ValueError(
            "Missing database settings: "
            + ", ".join(missing)
        )

    return URL.create(
        drivername="postgresql+psycopg",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ["POSTGRES_PORT"]),
        database=os.environ["POSTGRES_DB"],
    )