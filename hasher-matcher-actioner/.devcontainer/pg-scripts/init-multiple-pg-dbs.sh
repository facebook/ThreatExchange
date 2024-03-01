#!/bin/bash

set -eu

function user_exists() {
	local user=$1
	psql --username "$POSTGRES_USER" -tAc "SELECT 1 FROM pg_roles WHERE rolname='$user'" | grep -q 1
}

function database_exists() {
	local database=$1
	psql --username "$POSTGRES_USER" -tAc "SELECT 1 FROM pg_database WHERE datname='$database'" | grep -q 1
}

function create_user_and_database() {
	local database=$1
	echo "Creating user and database '$database'"
	if ! user_exists "$database"; then
		psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
		    CREATE USER $database;
EOSQL
	fi

	if ! database_exists "$database"; then
		psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
		    CREATE DATABASE $database;
		    GRANT ALL PRIVILEGES ON DATABASE $database TO $database;
EOSQL
	fi
}

if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
	echo "Multiple database creation requested: $POSTGRES_MULTIPLE_DATABASES"
	for db in $(echo "$POSTGRES_MULTIPLE_DATABASES" | tr ',' ' '); do
		create_user_and_database "$db"
	done
	echo "Multiple databases created"
fi
