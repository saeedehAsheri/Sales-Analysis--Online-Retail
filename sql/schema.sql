
CREATE SCHEMA IF NOT EXISTS retail;

CREATE TABLE IF NOT EXISTS retail.transactions (
    transaction_id BIGSERIAL PRIMARY KEY,

    source_row_id BIGINT NOT NULL UNIQUE,

    invoice_no VARCHAR(50) NOT NULL,
    stock_code VARCHAR(50) NOT NULL,
    description TEXT,

    quantity INTEGER NOT NULL,
    unit_price NUMERIC(14, 4) NOT NULL,
    total_price NUMERIC(18, 4) NOT NULL,

    invoice_date TIMESTAMP NOT NULL,
    customer_id VARCHAR(50),
    country VARCHAR(100),

    transaction_type VARCHAR(20) NOT NULL,

    loaded_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_transaction_type
        CHECK (
            transaction_type IN (
                'SALE',
                'CANCELLATION'
            )
        ),

    CONSTRAINT valid_unit_price
        CHECK (unit_price > 0),

    CONSTRAINT valid_quantity
        CHECK (
            (transaction_type = 'SALE'
                AND quantity > 0)
            OR
            (transaction_type = 'CANCELLATION'
                AND quantity < 0)
        )
);

CREATE INDEX IF NOT EXISTS idx_transactions_date
    ON retail.transactions (invoice_date);

CREATE INDEX IF NOT EXISTS idx_transactions_stock
    ON retail.transactions (stock_code);



CREATE TABLE IF NOT EXISTS retail.rejected_transactions (
    rejection_id BIGSERIAL PRIMARY KEY,

    source_row_id BIGINT NOT NULL UNIQUE,

    rejection_reasons TEXT[] NOT NULL,

    raw_data JSONB NOT NULL,

    rejected_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT rejection_reason_required
        CHECK (
            cardinality(rejection_reasons) > 0
        )
);
