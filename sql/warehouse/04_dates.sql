
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
