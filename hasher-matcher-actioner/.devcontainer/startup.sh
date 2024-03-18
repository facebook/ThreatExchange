#!/bin/bash
set -e
export OMM_CONFIG=/workspace/.devcontainer/omm_config.py
MIGRATION_COMMAND=1 flask --app OpenMediaMatch.app db upgrade --directory /workspace/src/OpenMediaMatch/migrations
flask --app OpenMediaMatch.app run --debug
