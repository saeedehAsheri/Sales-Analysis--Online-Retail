
-- Monthly gross sales and cancellation values
SELECT
    DATE_TRUNC('month', invoice_date)::DATE AS month,

    ROUND(
        SUM(total_price) FILTER (
            WHERE transaction_type = 'SALE'
        ), 2
    ) AS gross_sales,

    ROUND(
        COALESCE(
            SUM(total_price) FILTER (
                WHERE transaction_type = 'CANCELLATION'
            ),
            0
        ), 2
    ) AS cancellations,

    ROUND(SUM(total_price), 2) AS net_sales

FROM retail.transactions
GROUP BY 1
ORDER BY 1;

-- Top 10 products by gross revenue
SELECT
    stock_code,
    MAX(description) AS product_name,
    SUM(quantity) AS units_sold,
    ROUND(SUM(total_price), 2) AS revenue
FROM retail.transactions
WHERE transaction_type = 'SALE'
GROUP BY stock_code
ORDER BY revenue DESC
LIMIT 10;
