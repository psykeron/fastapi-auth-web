# Helpful Commands:

## format output

In postgresql shell
```
\pset format wrapped
```

## connecting to the server

In terminal
```bash
psql -U postgres -h host_name_of_the_database
```

# Creating A Database

Ensure that you have created your database.
It is not automated and needs to be done manually.

In postgresql shell
```sql
CREATE DATABASE your_database_name;
```

# Required Commands to Run:

## Set the timezone on your server

```sql
postgres=> ALTER DATABASE postgres SET timezone TO 'UTC';
```

# Granting Permissions:

## Giving permission to a service for a specific database

Note: All privileges.

```sql
postgres=> CREATE USER auth_service WITH PASSWORD 'insert_password';
postgres=> \c oly_auth

oly_auth=> GRANT ALL ON SCHEMA public TO auth_service;
oly_auth=> GRANT ALL ON ALL TABLES IN SCHEMA public TO auth_service;
oly_auth=> ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO auth_service;
```
