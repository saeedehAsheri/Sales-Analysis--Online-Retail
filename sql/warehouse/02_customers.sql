
INSERT INTO warehouse.dim_customer (customer_id)
SELECT DISTINCT customer_id
FROM retail.transactions
WHERE customer_id IS NOT NULL
ON CONFLICT (customer_id) DO NOTHING;

