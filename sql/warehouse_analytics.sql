
-- 1. Monthly sales KPIs from the warehouse.

SELECT
    d.year,
    d.month,
    TO_CHAR(d.date_key, 'YYYY-MM') AS sales_month,

    COUNT(*) FILTER (
        WHERE f.transaction_type = 'SALE'
    ) AS sale_lines,

    COUNT(*) FILTER (
        WHERE f.transaction_type = 'CANCELLATION'
    ) AS cancellation_lines,

    ROUND(
        COALESCE(
            SUM(f.total_price) FILTER (
                WHERE f.transaction_type = 'SALE'
            ), 0
        ), 2
    ) AS gross_sales,

    ROUND(
        ABS(COALESCE(
            SUM(f.total_price) FILTER (
                WHERE f.transaction_type = 'CANCELLATION'
            ), 0
        )), 2
    ) AS cancelled_value,

    ROUND(SUM(f.total_price), 2) AS net_sales

FROM warehouse.fact_sales AS f
JOIN warehouse.dim_date AS d
    ON f.date_key = d.date_key

GROUP BY d.year, d.month, sales_month
ORDER BY d.year, d.month;


-- 2. Top 10 merchandise products by gross revenue.

SELECT
    p.stock_code,
    p.product_name,

    SUM(f.quantity) AS units_sold,

    ROUND(
        SUM(f.total_price), 2
    ) AS gross_revenue

FROM warehouse.fact_sales AS f

JOIN warehouse.dim_product AS p
    ON f.product_key = p.product_key

WHERE f.transaction_type = 'SALE'
  AND p.stock_code NOT IN ('DOT', 'POST', 'M')
  AND p.product_name IS NOT NULL

GROUP BY p.stock_code, p.product_name
ORDER BY gross_revenue DESC
LIMIT 10;


-- 3. Top 10 identified customers by net transaction value.

SELECT
    c.customer_id,

    COUNT(DISTINCT f.invoice_no) FILTER (
        WHERE f.transaction_type = 'SALE'
    ) AS order_count,

    ROUND(SUM(f.total_price), 2) AS net_value

FROM warehouse.fact_sales AS f

JOIN warehouse.dim_customer AS c
    ON f.customer_key = c.customer_key

GROUP BY c.customer_id
ORDER BY net_value DESC
LIMIT 10;
