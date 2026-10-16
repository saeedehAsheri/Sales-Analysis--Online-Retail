
"""Generate sales reports from PostgreSQL."""

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from sales_pipeline.config import (
    PROJECT_ROOT,
    setup_logging,
)
from sales_pipeline.db import get_engine

logger = logging.getLogger(__name__)


def fetch_monthly_sales(engine: Engine) -> pd.DataFrame:
    """Read monthly sales from PostgreSQL."""
    sql_path = PROJECT_ROOT / "sql" / "monthly_sales.sql"
    query = sql_path.read_text(encoding="utf-8")

    with engine.connect() as connection:
        df = pd.read_sql_query(text(query), connection)

    if df.empty:
        raise ValueError("Monthly sales query returned no data")

    df["month"] = pd.to_datetime(df["month"])

    for column in [
        "gross_sales",
        "cancellations",
        "net_sales",
    ]:
        df[column] = pd.to_numeric(df[column])

    logger.info("Loaded %d monthly records", len(df))
    return df


def plot_monthly_sales(
    df: pd.DataFrame,
    output_path: Path,
) -> None:
    """Save a monthly net sales chart as a PNG file."""
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.bar(
        df["month"].dt.strftime("%Y-%m"),
        df["net_sales"],
    )

    ax.set_title("Monthly Net Sales")
    ax.set_xlabel("Month")
    ax.set_ylabel("Net Sales (GBP)")

    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", alpha=0.2)

    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)

    logger.info("Chart saved to %s", output_path)

def fetch_top_products(engine: Engine) -> pd.DataFrame:
    """Fetch the top-selling products from PostgreSQL."""
    sql_path = PROJECT_ROOT / "sql" / "top_products.sql"

    query = sql_path.read_text(encoding="utf-8")

    with engine.connect() as connection:
        df = pd.read_sql_query(text(query), connection)

    if df.empty:
        raise ValueError("Top products query returned no data")

    df["revenue"] = pd.to_numeric(df["revenue"])
    df["units_sold"] = pd.to_numeric(df["units_sold"])

    logger.info("Loaded %d top products", len(df))

    return df



def plot_top_products(
    df: pd.DataFrame,
    output_path: Path,
) -> None:
    """Create and save a top-products revenue chart."""
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = df.sort_values("revenue", ascending=True)

    fig, ax = plt.subplots(figsize=(12, 7))

    ax.barh(
        data["product_name"],
        data["revenue"],
    )

    ax.set_title("Top 10 Products by Revenue")
    ax.set_xlabel("Revenue (GBP)")
    ax.set_ylabel("Product")

    ax.grid(axis="x", alpha=0.2)

    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)

    logger.info("Top products chart saved to %s", output_path)


def fetch_sales_by_country(engine: Engine) -> pd.DataFrame:
    """Fetch revenue grouped by country."""
    sql_path = PROJECT_ROOT / "sql" / "sales_by_country.sql"
    query = sql_path.read_text(encoding="utf-8")

    with engine.connect() as connection:
        df = pd.read_sql_query(text(query), connection)

    if df.empty:
        raise ValueError("Country sales query returned no data")

    df["gross_revenue"] = pd.to_numeric(df["gross_revenue"])
    return df


def plot_sales_by_country(
    df: pd.DataFrame,
    output_path: Path,
) -> None:
    """Save a chart of the highest-revenue countries."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = df.sort_values("gross_revenue")

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.barh(data["country"], data["gross_revenue"])

    ax.set_title("Top 10 Countries by Gross Revenue")
    ax.set_xlabel("Gross Revenue (GBP)")
    ax.grid(axis="x", alpha=0.2)

    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def plot_cancellations(
    df: pd.DataFrame,
    output_path: Path,
) -> None:
    """Save monthly cancellation value percentages."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.bar(
        df["month"].dt.strftime("%Y-%m"),
        df["cancellation_value_pct"],
    )

    ax.set_title("Monthly Cancellation Value Ratio")
    ax.set_xlabel("Month")
    ax.set_ylabel("Cancellation Value / Gross Sales (%)")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", alpha=0.2)

    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def fetch_cancellations(engine: Engine) -> pd.DataFrame:
    """Fetch monthly cancellation statistics."""
    sql_path = PROJECT_ROOT / "sql" / "cancellations.sql"
    query = sql_path.read_text(encoding="utf-8")

    with engine.connect() as connection:
        df = pd.read_sql_query(text(query), connection)

    if df.empty:
        raise ValueError("Cancellation query returned no data")

    df["month"] = pd.to_datetime(df["month"])
    df["cancellation_value_pct"] = pd.to_numeric(
        df["cancellation_value_pct"]
    )

    return df


def plot_international_sales(
    df: pd.DataFrame,
    output_path: Path,
) -> None:
    """Compare revenue outside the United Kingdom."""
    data = df.loc[
        df["country"] != "United Kingdom"
    ].copy()

    if data.empty:
        raise ValueError("No international sales available")

    data = data.sort_values("gross_revenue")

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig, ax = plt.subplots(figsize=(11, 6))

    ax.barh(
        data["country"],
        data["gross_revenue"],
    )

    ax.set_title("Top International Markets")
    ax.set_xlabel("Gross Revenue (GBP)")
    ax.grid(axis="x", alpha=0.2)

    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)



def main() -> int:
    """Generate monthly sales and top-products reports."""
    setup_logging()
    engine = None

    try:
        engine = get_engine()

        output_dir = PROJECT_ROOT / "reports" / "figures"

        monthly_df = fetch_monthly_sales(engine)
        plot_monthly_sales(
            monthly_df,
            output_dir / "monthly_sales.png",
        )

        products_df = fetch_top_products(engine)
        plot_top_products(
            products_df,
            output_dir / "top_products.png",
        )

        country_df = fetch_sales_by_country(engine)
        plot_sales_by_country(
            country_df,
            output_dir / "sales_by_country.png",
        )
        plot_international_sales(
            country_df,
            output_dir / "international_sales.png",
        )
        cancellations_df = fetch_cancellations(engine)
        plot_cancellations(
            cancellations_df,
            output_dir / "cancellations.png",
        )


        logger.info("All reports generated successfully")
        return 0

    except Exception:
        logger.exception("Reporting failed")
        return 1

    finally:
        if engine is not None:
            engine.dispose()



if __name__ == "__main__":
    raise SystemExit(main())
