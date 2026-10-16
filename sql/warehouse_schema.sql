
-- Analytical star schema for Online Retail.
-- Grain: one source transaction line per fact row.

BEGIN;

CREATE SCHEMA IF NOT EXISTS warehouse;

CREATE TABLE IF NOT EXISTS warehouse.dim_product (
    product_key BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    stock_code TEXT NOT NULL UNIQUE,
    product_name TEXT
);

CREATE TABLE IF NOT EXISTS warehouse.dim_customer (
    customer_key BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    customer_id TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS warehouse.dim_country (
    country_key BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    country_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS warehouse.dim_date (
    date_key DATE PRIMARY KEY,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    day INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.fact_sales (
    sales_key BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    transaction_id BIGINT NOT NULL UNIQUE
        REFERENCES retail.transactions(transaction_id),

    product_key BIGINT NOT NULL
        REFERENCES warehouse.dim_product(product_key),

    customer_key BIGINT
        REFERENCES warehouse.dim_customer(customer_key),

    country_key BIGINT
        REFERENCES warehouse.dim_country(country_key),

    date_key DATE NOT NULL
        REFERENCES warehouse.dim_date(date_key),

    invoice_no TEXT NOT NULL,
    invoice_date TIMESTAMP NOT NULL,

    transaction_type TEXT NOT NULL
        CHECK (
            transaction_type IN ('SALE', 'CANCELLATION')
        ),

    quantity INTEGER NOT NULL,
    unit_price NUMERIC(14, 4) NOT NULL,
    total_price NUMERIC(18, 4) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_fact_sales_date
    ON warehouse.fact_sales(date_key);

CREATE INDEX IF NOT EXISTS idx_fact_sales_product
    ON warehouse.fact_sales(product_key);

CREATE INDEX IF NOT EXISTS idx_fact_sales_customer
    ON warehouse.fact_sales(customer_key);

CREATE INDEX IF NOT EXISTS idx_fact_sales_country
    ON warehouse.fact_sales(country_key);

COMMIT;
