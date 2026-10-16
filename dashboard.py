
"""Interactive retail sales analytics dashboard."""

from datetime import timedelta

import pandas as pd
import streamlit as st
from sqlalchemy import text

from sales_pipeline.db import get_engine



FILTER_SQL = """
WITH filtered AS (
    SELECT f.*
    FROM warehouse.fact_sales AS f
    LEFT JOIN warehouse.dim_country AS c
        ON f.country_key = c.country_key
    WHERE f.invoice_date >= :start_date
      AND f.invoice_date < :end_exclusive
      AND (
          :country = 'All Countries'
          OR c.country_name = :country
      )
)
"""


@st.cache_data(ttl=300)
def load_filters() -> tuple[pd.Timestamp, pd.Timestamp, list[str]]:
    """Fetch date boundaries and available countries."""
    engine = get_engine()

    try:
        with engine.connect() as connection:
            dates = connection.execute(text("""
                SELECT
                    MIN(invoice_date)::DATE AS min_date,
                    MAX(invoice_date)::DATE AS max_date
                FROM warehouse.fact_sales
            """)).one()

            countries = connection.execute(text("""
                SELECT country_name
                FROM warehouse.dim_country
                ORDER BY country_name
            """)).scalars().all()

    finally:
        engine.dispose()

    if dates.min_date is None or dates.max_date is None:
        raise ValueError("Warehouse does not contain sales data")

    return (
        pd.Timestamp(dates.min_date),
        pd.Timestamp(dates.max_date),
        ["All Countries", *countries],
    )


@st.cache_data(ttl=300)
def load_dashboard_data(
    start_date: str,
    end_date: str,
    country: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Fetch filtered KPIs, trends, products, and customers."""
    params = {
        "start_date": start_date,
        "end_exclusive": str(
            pd.Timestamp(end_date) + timedelta(days=1)
        ),
        "country": country,
    }


    kpi_sql = FILTER_SQL + """
        SELECT
            COUNT(DISTINCT f.invoice_no) FILTER (
                WHERE f.transaction_type = 'SALE'
            ) AS total_orders,
            COALESCE(SUM(f.total_price) FILTER (
                WHERE f.transaction_type = 'SALE'
            ), 0) AS gross_sales,
            ABS(COALESCE(SUM(f.total_price) FILTER (
                WHERE f.transaction_type = 'CANCELLATION'
            ), 0)) AS cancellations,
            COALESCE(SUM(f.total_price), 0) AS net_sales
        FROM filtered AS f
    """

    monthly_sql = FILTER_SQL + """
        SELECT
            DATE_TRUNC('month', f.invoice_date)::DATE AS month,
            SUM(f.total_price) AS net_sales
        FROM filtered AS f
        GROUP BY 1
        ORDER BY 1
    """

    products_sql = FILTER_SQL + """
        SELECT
            p.stock_code,
            p.product_name,
            SUM(f.total_price) AS revenue
        FROM filtered AS f
        JOIN warehouse.dim_product AS p
            ON f.product_key = p.product_key
        WHERE f.transaction_type = 'SALE'
          AND p.stock_code NOT IN ('DOT', 'POST', 'M')
        GROUP BY p.stock_code, p.product_name
        ORDER BY revenue DESC
        LIMIT 10
    """

    customers_sql = FILTER_SQL + """
        SELECT
            cu.customer_id,
            SUM(f.total_price) AS net_value
        FROM filtered AS f
        JOIN warehouse.dim_customer AS cu
            ON f.customer_key = cu.customer_key
        GROUP BY cu.customer_id
        ORDER BY net_value DESC
        LIMIT 10
    """


    engine = get_engine()

    try:
        with engine.connect() as connection:
            kpis = pd.read_sql_query(
                text(kpi_sql), connection, params=params
            )
            monthly = pd.read_sql_query(
                text(monthly_sql), connection, params=params
            )
            products = pd.read_sql_query(
                text(products_sql), connection, params=params
            )
            customers = pd.read_sql_query(
                text(customers_sql), connection, params=params
            )
    finally:
        engine.dispose()

    return kpis, monthly, products, customers


def main() -> None:
    """Render the interactive retail analytics dashboard."""
    st.set_page_config(
        page_title="Retail Analytics Dashboard",
        page_icon="📊",
        layout="wide",
    )

    st.title("Retail Sales Analytics Dashboard")
    st.caption("PostgreSQL | Star Schema | Python | Streamlit")

    try:
        min_date, max_date, countries = load_filters()
    except Exception:
        st.error("Could not load warehouse filters.")
        st.stop()

    st.sidebar.header("Filters")

    selected_dates = st.sidebar.date_input(
        "Date Range",
        value=(min_date.date(), max_date.date()),
        min_value=min_date.date(),
        max_value=max_date.date(),
    )

    selected_country = st.sidebar.selectbox(
        "Country",
        options=countries,
    )

    if len(selected_dates) != 2:
        st.info("Please select a start and end date.")
        st.stop()

    start_date, end_date = selected_dates

    if start_date > end_date:
        st.error("Start date must be before end date.")
        st.stop()

    if st.sidebar.button("Refresh Data"):
        load_filters.clear()
        load_dashboard_data.clear()
        st.rerun()

    try:
        kpis, monthly, products, customers = load_dashboard_data(
            str(start_date),
            str(end_date),
            selected_country,
        )
    except Exception:
        st.error("Could not load dashboard data.")
        st.stop()

    summary = kpis.iloc[0]

    gross_sales = float(summary["gross_sales"])
    cancellations = float(summary["cancellations"])
    net_sales = float(summary["net_sales"])
    total_orders = int(summary["total_orders"])

    st.subheader("Key Performance Indicators")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Gross Sales", f"£{gross_sales:,.2f}")
    col2.metric(
        "Cancellation Value",
        f"£{cancellations:,.2f}",
    )
    col3.metric("Net Sales", f"£{net_sales:,.2f}")
    col4.metric("Orders", f"{total_orders:,}")

    if monthly.empty:
        st.warning("No transactions for the selected filters.")
        return

    monthly["month"] = pd.to_datetime(monthly["month"])
    monthly["net_sales"] = pd.to_numeric(
        monthly["net_sales"]
    )

    st.subheader("Monthly Net Sales")
    st.line_chart(
        monthly.set_index("month")["net_sales"],
    )

    left, right = st.columns(2)

    with left:
        st.subheader("Top Products")

        if not products.empty:
            products["revenue"] = pd.to_numeric(
                products["revenue"]
            )
            st.bar_chart(
                products.set_index("product_name")["revenue"],
                horizontal=True,
            )
        else:
            st.info("No products for this selection.")

    with right:
        st.subheader("Top Customers")

        if not customers.empty:
            customers["net_value"] = pd.to_numeric(
                customers["net_value"]
            )
            st.bar_chart(
                customers.set_index("customer_id")["net_value"],
                horizontal=True,
            )
        else:
            st.info("No identified customers for this selection.")


if __name__ == "__main__":
    main()
