
INSERT INTO warehouse.dim_product (
    stock_code,
    product_name
)
SELECT
    stock_code,
    MAX(description)
FROM retail.transactions
GROUP BY stock_code
ON CONFLICT (stock_code) DO NOTHING;
