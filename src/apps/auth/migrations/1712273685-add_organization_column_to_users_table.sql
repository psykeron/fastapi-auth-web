-- Migration: add_organization_column_to_users_table
-- Created at: 2024-04-05 01:34:45
-- ====  UP  ====

BEGIN;
    ALTER TABLE users
        ADD COLUMN organization_id VARCHAR(255),
        ADD CONSTRAINT fk_users_organization_id FOREIGN KEY (organization_id) REFERENCES organizations (id);
COMMIT;

-- ==== DOWN ====

BEGIN;
    ALTER TABLE users
        DROP COLUMN organization_id;
COMMIT;
