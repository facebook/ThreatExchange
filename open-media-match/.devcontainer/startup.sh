#!/bin/bash
set -e
export OMM_CONFIG=/workspace/.devcontainer/omm_config.py
flask --app OpenMediaMatch.app db upgrade --directory /workspace/src/openMediaMatch/migrations
flask --app OpenMediaMatch.app run --debug
