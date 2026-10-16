
-- Normalize legacy numeric CustomerIDs.
-- Example: '17068.0' -> '17068'
-- Preserves NULLs and all other customer IDs.

BEGIN;

SET LOCAL lock_timeout = '10s';
SET LOCAL statement_timeout = '5min';

DO $$
DECLARE
    affected_count BIGINT;
BEGIN
    SELECT COUNT(*)
    INTO affected_count
    FROM retail.transactions
    WHERE customer_id ~ '^[0-9]+[.]0$';

    RAISE NOTICE
        'Customer IDs to normalize: %',
        affected_count;
END $$;

UPDATE retail.transactions
SET customer_id = LEFT(
    customer_id,
    LENGTH(customer_id) - 2
)
WHERE customer_id ~ '^[0-9]+[.]0$';

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM retail.transactions
        WHERE customer_id ~ '^[0-9]+[.]0$'
    ) THEN
        RAISE EXCEPTION
            'Customer ID normalization incomplete';
    END IF;
END $$;

COMMIT;
