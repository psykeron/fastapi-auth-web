-- Migration: make_organization_name_unique
-- Created at: 2024-05-27 18:18:52
-- ====  UP  ====

BEGIN;

ALTER TABLE organizations
  ADD CONSTRAINT organizations_name_key UNIQUE (name);

COMMIT;

-- ==== DOWN ====

BEGIN;

ALTER TABLE organizations
  DROP CONSTRAINT organizations_name_key;

COMMIT;
