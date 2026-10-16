
-- Top 10 countries by gross sales revenue

SELECT
    country,
    COUNT(DISTINCT invoice_no) AS total_orders,
    ROUND(SUM(total_price), 2) AS gross_revenue
FROM retail.transactions
WHERE transaction_type = 'SALE'
  AND country IS NOT NULL
GROUP BY country
ORDER BY gross_revenue DESC
LIMIT 10;
