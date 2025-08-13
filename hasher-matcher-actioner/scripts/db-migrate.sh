#!/bin/sh

MIGRATION_COMMAND=1 OMM_SQLALCHEMY_ENGINE_LOG_LEVEL=INFO flask --app OpenMediaMatch.app db upgrade --directory OpenMediaMatch/migrations
