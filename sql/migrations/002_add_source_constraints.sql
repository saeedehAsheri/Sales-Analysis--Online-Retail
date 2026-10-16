
-- Add source file integrity constraints.
-- Keep the old source_row_id UNIQUE constraint for now.

BEGIN;

SET LOCAL lock_timeout = '10s';

-- Ensure no rows are missing source file IDs.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM retail.transactions
        WHERE source_file_id IS NULL
    ) OR EXISTS (
        SELECT 1
        FROM retail.rejected_transactions
        WHERE source_file_id IS NULL
    ) THEN
        RAISE EXCEPTION
            'Backfill incomplete: NULL source_file_id found';
    END IF;
END $$;

-- A source file ID is now mandatory.
ALTER TABLE retail.transactions
    ALTER COLUMN source_file_id SET NOT NULL;

ALTER TABLE retail.rejected_transactions
    ALTER COLUMN source_file_id SET NOT NULL;

-- Every source_file_id must reference an existing file.
ALTER TABLE retail.transactions
    ADD CONSTRAINT fk_transactions_source_file
    FOREIGN KEY (source_file_id)
    REFERENCES retail.source_files(source_file_id);

ALTER TABLE retail.rejected_transactions
    ADD CONSTRAINT fk_rejected_source_file
    FOREIGN KEY (source_file_id)
    REFERENCES retail.source_files(source_file_id);

-- The combination of file ID and row number must be unique.
ALTER TABLE retail.transactions
    ADD CONSTRAINT uq_transactions_source_row
    UNIQUE (source_file_id, source_row_id);

ALTER TABLE retail.rejected_transactions
    ADD CONSTRAINT uq_rejected_source_row
    UNIQUE (source_file_id, source_row_id);

COMMIT;
