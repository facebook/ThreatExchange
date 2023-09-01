#!/bin/bash
set -e
export OMM_CONFIG=/workspace/.devcontainer/omm_config.py
flask --app OpenMediaMatch db upgrade --directory src/openMediaMatch/migrations
flask --app OpenMediaMatch run --debug
