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

for migration_dir in `find ../src/apps -type d -maxdepth 2 -name migrations`; do
    appname=$(echo $migration_dir | awk -F'/' '{print $4}');
    shmig -d oly_$appname$db_suffix -t postgresql -H $DB_HOST -l $DB_USER -p $DB_PASSWORD -m $migration_dir up;
done;
