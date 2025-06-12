#!/bin/sh

MIGRATION_COMMAND=1 flask --app OpenMediaMatch.app db upgrade --directory OpenMediaMatch/migrations