
-- Top 10 products by gross sales revenue.
-- Exclude known postage and manual adjustment codes.

SELECT
    stock_code,
    MAX(description) AS product_name,
    SUM(quantity) AS units_sold,
    ROUND(SUM(total_price), 2) AS revenue
FROM retail.transactions
WHERE transaction_type = 'SALE'
  AND stock_code NOT IN ('DOT', 'POST', 'M')
  AND description IS NOT NULL
GROUP BY stock_code
ORDER BY revenue DESC
LIMIT 10;
