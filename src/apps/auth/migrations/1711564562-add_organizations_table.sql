-- Migration: add_organizations_table
-- Created at: 2024-03-27 19:36:02
-- ====  UP  ====

BEGIN;

CREATE TABLE organizations (
    id VARCHAR(32) NOT NULL,
    name VARCHAR(512) NOT NULL,
    role VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id)
);

COMMIT;

-- ==== DOWN ====

BEGIN;

DROP TABLE organizations;

COMMIT;
