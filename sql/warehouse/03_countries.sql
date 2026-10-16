
INSERT INTO warehouse.dim_country (country_name)
SELECT DISTINCT country
FROM retail.transactions
WHERE country IS NOT NULL
ON CONFLICT (country_name) DO NOTHING;
