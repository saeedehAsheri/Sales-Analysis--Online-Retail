
"""Tests for sales reporting."""

import matplotlib
import pandas as pd

from sales_pipeline.reporting import (
    plot_cancellations,
    plot_monthly_sales,
    plot_sales_by_country,
    plot_top_products,
)


def test_plot_monthly_sales(tmp_path) -> None:
    """Verify that the monthly chart is generated."""
    df = pd.DataFrame({
        "month": pd.to_datetime([
            "2011-01-01",
            "2011-02-01",
        ]),
        "net_sales": [1000.0, 1500.0],
    })

    output = tmp_path / "figures" / "monthly_sales.png"

    plot_monthly_sales(df, output)

    assert output.exists()
    assert output.stat().st_size > 0
    assert matplotlib.get_backend().lower() == "agg"



def test_plot_top_products(tmp_path) -> None:
    """Verify that the top-products chart is saved."""
    df = pd.DataFrame({
        "product_name": [
            "Product A",
            "Product B",
            "Product C",
        ],
        "revenue": [
            1500.0,
            1000.0,
            750.0,
        ],
    })

    output = tmp_path / "figures" / "top_products.png"

    plot_top_products(df, output)

    assert output.exists()
    assert output.stat().st_size > 0


def test_plot_sales_by_country(tmp_path) -> None:
    """Verify country chart creation."""
    df = pd.DataFrame({
        "country": ["United Kingdom", "France"],
        "gross_revenue": [10000.0, 2000.0],
    })

    output = tmp_path / "countries.png"
    plot_sales_by_country(df, output)

    assert output.is_file()
    assert output.stat().st_size > 0


def test_plot_cancellations(tmp_path) -> None:
    """Verify cancellation chart creation."""
    df = pd.DataFrame({
        "month": pd.to_datetime([
            "2011-01-01",
            "2011-02-01",
        ]),
        "cancellation_value_pct": [5.0, 8.0],
    })

    output = tmp_path / "cancellations.png"
    plot_cancellations(df, output)

    assert output.is_file()
    assert output.stat().st_size > 0
