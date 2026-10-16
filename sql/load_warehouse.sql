
-- Populate warehouse dimensions and facts.
-- Re-running this script must not duplicate existing rows.

BEGIN;

-- 1. Products
INSERT INTO warehouse.dim_product (
    stock_code,
    product_name
)
SELECT
    stock_code,
    MAX(description) AS product_name
FROM retail.transactions
GROUP BY stock_code
ON CONFLICT (stock_code) DO NOTHING;


-- 2. Customers
INSERT INTO warehouse.dim_customer (customer_id)
SELECT DISTINCT customer_id
FROM retail.transactions
WHERE customer_id IS NOT NULL
ON CONFLICT (customer_id) DO NOTHING;


-- 3. Countries
INSERT INTO warehouse.dim_country (country_name)
SELECT DISTINCT country
FROM retail.transactions
WHERE country IS NOT NULL
ON CONFLICT (country_name) DO NOTHING;


-- 4. Calendar dates
INSERT INTO warehouse.dim_date (
    date_key,
    year,
    quarter,
    month,
    month_name,
    day,
    day_of_week
)
SELECT DISTINCT
    invoice_date::DATE,
    EXTRACT(YEAR FROM invoice_date)::INTEGER,
    EXTRACT(QUARTER FROM invoice_date)::INTEGER,
    EXTRACT(MONTH FROM invoice_date)::INTEGER,
    TO_CHAR(invoice_date, 'FMMonth'),
    EXTRACT(DAY FROM invoice_date)::INTEGER,
    EXTRACT(ISODOW FROM invoice_date)::INTEGER
FROM retail.transactions
ON CONFLICT (date_key) DO NOTHING;


-- 5. Fact table
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

COMMIT;
