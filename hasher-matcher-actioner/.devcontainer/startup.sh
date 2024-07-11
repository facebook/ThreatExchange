#!/bin/bash
set -e
export OMM_CONFIG=/workspace/reference_omm_configs/development_omm_config.py
MIGRATION_COMMAND=1 flask --app src/OpenMediaMatch.app db upgrade --directory /workspace/src/OpenMediaMatch/migrations
flask --app src/OpenMediaMatch.app run --debug
