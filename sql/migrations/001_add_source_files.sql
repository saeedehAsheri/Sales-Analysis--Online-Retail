
-- Add source file tracking without deleting existing data.

BEGIN;

CREATE TABLE IF NOT EXISTS retail.source_files (
    source_file_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    file_hash VARCHAR(64) NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_file_hash
        CHECK (file_hash ~ '^[0-9a-f]{64}$')
);

ALTER TABLE retail.transactions
    ADD COLUMN IF NOT EXISTS source_file_id BIGINT;

ALTER TABLE retail.rejected_transactions
    ADD COLUMN IF NOT EXISTS source_file_id BIGINT;

COMMIT;
