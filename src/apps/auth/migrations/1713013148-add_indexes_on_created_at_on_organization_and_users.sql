-- Migration: add_indexes_on_created_at_on_organization_and_users
-- Created at: 2024-04-13 14:59:08
-- ====  UP  ====

BEGIN;

CREATE INDEX index_organizations_on_created_at ON organizations (created_at);
CREATE INDEX index_users_on_created_at ON users (created_at);

COMMIT;

-- ==== DOWN ====

BEGIN;

DROP INDEX index_organizations_on_created_at;
DROP INDEX index_users_on_created_at;

COMMIT;
