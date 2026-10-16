
-- ============================================================
-- Retail Sales Data Engineering Pipeline
-- Database Bootstrap
--
-- Creates the final database structure on a NEW database.
-- Does not import data or run legacy migrations.
-- ============================================================

BEGIN;

-- Safety check: bootstrap is only for a fresh database.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_namespace
        WHERE nspname IN ('retail', 'warehouse')
    ) THEN
        RAISE EXCEPTION
            'Bootstrap requires a fresh database. '
            'Retail or warehouse schema already exists.';
    END IF;
END $$;


-- ============================================================
-- 1. RETAIL SCHEMA
-- ============================================================

CREATE SCHEMA retail;


-- Source file registry
CREATE TABLE retail.source_files (
    source_file_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    file_hash VARCHAR(64) NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_file_hash
        CHECK (file_hash ~ '^[0-9a-f]{64}$')
);


-- Clean transactions
CREATE TABLE retail.transactions (
    transaction_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    source_file_id BIGINT NOT NULL
        REFERENCES retail.source_files(source_file_id),

    source_row_id BIGINT NOT NULL,

    invoice_no TEXT NOT NULL,
    stock_code TEXT NOT NULL,
    description TEXT,

    quantity INTEGER NOT NULL,
    unit_price NUMERIC(14, 4) NOT NULL,
    total_price NUMERIC(18, 4) NOT NULL,

    invoice_date TIMESTAMP NOT NULL,
    customer_id TEXT,
    country TEXT,

    transaction_type TEXT NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_transactions_source_row
        UNIQUE (source_file_id, source_row_id),

    CONSTRAINT valid_unit_price
        CHECK (unit_price > 0),

    CONSTRAINT valid_transaction_type
        CHECK (
            transaction_type IN (
                'SALE',
                'CANCELLATION'
            )
        ),

    CONSTRAINT valid_transaction_quantity
        CHECK (
            (
                transaction_type = 'SALE'
                AND quantity > 0
            )
            OR
            (
                transaction_type = 'CANCELLATION'
                AND quantity < 0
            )
        )
);


-- Rejected transactions and quality reasons
CREATE TABLE retail.rejected_transactions (
    rejection_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    source_file_id BIGINT NOT NULL
        REFERENCES retail.source_files(source_file_id),

    source_row_id BIGINT NOT NULL,

    rejection_reasons TEXT[] NOT NULL,
    raw_data JSONB NOT NULL,

    rejected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_rejected_source_row
        UNIQUE (source_file_id, source_row_id),

    CONSTRAINT valid_rejection_reasons
        CHECK (CARDINALITY(rejection_reasons) > 0)
);


-- Retail indexes
CREATE INDEX idx_transactions_invoice_date
    ON retail.transactions(invoice_date);

CREATE INDEX idx_transactions_stock_code
    ON retail.transactions(stock_code);

CREATE INDEX idx_transactions_customer_id
    ON retail.transactions(customer_id);


-- ============================================================
-- 2. WAREHOUSE SCHEMA
-- ============================================================

CREATE SCHEMA warehouse;


-- Product dimension
CREATE TABLE warehouse.dim_product (
    product_key BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    stock_code TEXT NOT NULL UNIQUE,
    product_name TEXT
);


-- Customer dimension
CREATE TABLE warehouse.dim_customer (
    customer_key BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    customer_id TEXT NOT NULL UNIQUE
);


-- Country dimension
CREATE TABLE warehouse.dim_country (
    country_key BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    country_name TEXT NOT NULL UNIQUE
);


-- Date dimension
CREATE TABLE warehouse.dim_date (
    date_key DATE PRIMARY KEY,

    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name TEXT NOT NULL,

    day INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL
);


-- Central fact table
CREATE TABLE warehouse.fact_sales (
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
            transaction_type IN (
                'SALE',
                'CANCELLATION'
            )
        ),

    quantity INTEGER NOT NULL,
    unit_price NUMERIC(14, 4) NOT NULL,
    total_price NUMERIC(18, 4) NOT NULL
);


-- Warehouse indexes
CREATE INDEX idx_fact_sales_date
    ON warehouse.fact_sales(date_key);

CREATE INDEX idx_fact_sales_product
    ON warehouse.fact_sales(product_key);

CREATE INDEX idx_fact_sales_customer
    ON warehouse.fact_sales(customer_key);

CREATE INDEX idx_fact_sales_country
    ON warehouse.fact_sales(country_key);


COMMIT;
