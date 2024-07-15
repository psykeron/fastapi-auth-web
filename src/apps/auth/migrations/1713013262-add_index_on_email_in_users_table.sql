-- Migration: add_index_on_email_in_users_table
-- Created at: 2024-04-13 15:01:02
-- ====  UP  ====

BEGIN;

CREATE INDEX index_users_on_email ON users (email);

COMMIT;

-- ==== DOWN ====

BEGIN;

DROP INDEX index_users_on_email;

COMMIT;
