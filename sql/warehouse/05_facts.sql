
INSERT INTO warehouse.fact_sales (
    transaction_id,
    product_key,
    customer_key,
    country_key,
    date_key,
    invoice_no,
    invoice_date,
    transaction_type,
    quantity,
    unit_price,
    total_price
)
SELECT
    t.transaction_id,
    p.product_key,
    c.customer_key,
    co.country_key,
    d.date_key,
    t.invoice_no,
    t.invoice_date,
    t.transaction_type,
    t.quantity,
    t.unit_price,
    t.total_price
FROM retail.transactions AS t
JOIN warehouse.dim_product AS p
    ON t.stock_code = p.stock_code
JOIN warehouse.dim_date AS d
    ON t.invoice_date::DATE = d.date_key
LEFT JOIN warehouse.dim_customer AS c
    ON t.customer_id = c.customer_id
LEFT JOIN warehouse.dim_country AS co
    ON t.country = co.country_name
ON CONFLICT (transaction_id) DO NOTHING;
