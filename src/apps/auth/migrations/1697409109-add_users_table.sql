-- Migration: add_users_table
-- Created at: 2023-10-16 00:31:49
-- ====  UP  ====

BEGIN;

CREATE TABLE users (
    id VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    first_name VARCHAR(255) DEFAULT NULL,
    last_name VARCHAR(255) DEFAULT NULL,
    is_activated BOOLEAN NOT NULL DEFAULT FALSE,
    is_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    confirmation_token VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id),
    UNIQUE (email)
);

COMMIT;

-- ==== DOWN ====

BEGIN;

DROP TABLE users;

COMMIT;
