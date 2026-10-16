
-- Remove legacy single-column uniqueness constraints.
-- Preserve composite uniqueness and primary keys.

BEGIN;

SET LOCAL lock_timeout = '10s';

DO $$
DECLARE
    target_table TEXT;
    old_constraint TEXT;
    constraint_count INTEGER;
BEGIN
    FOREACH target_table IN ARRAY ARRAY[
        'transactions',
        'rejected_transactions'
    ]
    LOOP
        SELECT COUNT(*), MIN(c.conname)
        INTO constraint_count, old_constraint
        FROM pg_constraint c
        JOIN pg_attribute a
          ON a.attrelid = c.conrelid
         AND a.attname = 'source_row_id'
        WHERE c.conrelid = format(
            'retail.%I', target_table
        )::regclass
          AND c.contype = 'u'
          AND c.conkey = ARRAY[a.attnum]::SMALLINT[];

        IF constraint_count != 1 THEN
            RAISE EXCEPTION
                'Expected one legacy unique constraint on %, found %',
                target_table,
                constraint_count;
        END IF;

        EXECUTE format(
            'ALTER TABLE retail.%I DROP CONSTRAINT %I',
            target_table,
            old_constraint
        );
    END LOOP;
END $$;

COMMIT;
