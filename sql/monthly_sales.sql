
SELECT
    DATE_TRUNC('month', invoice_date)::DATE AS month,

    COALESCE(
        SUM(total_price) FILTER (
            WHERE transaction_type = 'SALE'
        ), 0
    ) AS gross_sales,

    COALESCE(
        SUM(total_price) FILTER (
            WHERE transaction_type = 'CANCELLATION'
        ), 0
    ) AS cancellations,

    SUM(total_price) AS net_sales

FROM retail.transactions
GROUP BY 1
ORDER BY 1;
