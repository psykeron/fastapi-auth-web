#!/bin/bash

trap 'error_handler' ERR

error_handler() {
    exit_code=$1
    if [ $exit_code -eq 1 ]; then
        echo "Command failed with exit code 1. Exiting."
        exit 1
    fi
}

db_suffix=""
db_superuser="postgres"

case $1 in
  test)
    echo "Setting up database with test configuration"
    DB_USER='test_user'
    DB_PASSWORD='test_password'
    db_suffix="_test"
    ;;
  *)
    echo "Setting up database with environment specific configuration"
    ;;
esac


# start of arg validity checks #
if [[ -z $DB_USER ]]; then
    echo "The DB_USER env var is required."
    exit 1
fi

if [[ -z $DB_PASSWORD ]]; then
    echo "The DB_PASSWORD env var is required."
    exit 1
fi

if [[ -z $DB_HOST ]]; then
    echo "The DB_HOST env var is required."
    exit 1
fi
# end of arg validity checks #

# Check if the superuser exists
if psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$db_superuser'" | grep -q 1; then
    echo "Superuser '$db_superuser' exists."
else
    echo "Superuser '$db_superuser' does not exist. Creating $db_superuser"
    createuser -s postgres
fi

# Check if the db_user exists
if psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1; then
    echo "DB user '$DB_USER' exists."
else
    echo "DB user '$DB_USER' does not exist. Creating $DB_USER"
    createuser $DB_USER
fi

# search for apps that have migrations folders
for migration_dir in `find ../src/apps -type d -maxdepth 2 -name migrations`; do
    appname=$(echo $migration_dir | awk -F'/' '{print $4}');

	echo ""
    echo "Setting up database for app $appname."

    # create database
    if psql -tAl | grep -qw oly_$appname$db_suffix; then
    	echo "DB exists oly_$appname$db_suffix"
	else
		createdb oly_$appname$db_suffix
	fi

	# grant correct permissions to users for each schema
	echo "Setting user permissions for user ${DB_USER} on database schema"
	psql -U $db_superuser -d oly_$appname$db_suffix -c "ALTER USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';"
	psql -U $db_superuser -d oly_$appname$db_suffix -c "GRANT ALL ON SCHEMA public TO ${DB_USER};"
	psql -U $db_superuser -d oly_$appname$db_suffix -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ${DB_USER};"

	echo "Finished setting up database for app $appname."
	echo "********"
	echo ""
done;