
-- Monthly cancellation value relative to gross sales

SELECT
    DATE_TRUNC('month', invoice_date)::DATE AS month,

    ROUND(
        COALESCE(
            SUM(total_price) FILTER (
                WHERE transaction_type = 'SALE'
            ), 0
        ), 2
    ) AS gross_sales,

    ROUND(
        ABS(COALESCE(
            SUM(total_price) FILTER (
                WHERE transaction_type = 'CANCELLATION'
            ), 0
        )), 2
    ) AS cancelled_value,

    ROUND(
        100.0 * ABS(COALESCE(
            SUM(total_price) FILTER (
                WHERE transaction_type = 'CANCELLATION'
            ), 0
        ))
        / NULLIF(
            SUM(total_price) FILTER (
                WHERE transaction_type = 'SALE'
            ), 0
        ), 2
    ) AS cancellation_value_pct

FROM retail.transactions
GROUP BY 1
ORDER BY 1;
