#!/usr/bin/env bash
# If a collaboration json exist write the items into aws
# Argument 1 should be name of collab table to write to
if test -f collabs.json; then
    cat collabs.json | jq "{ $1 : . }" > aws_collab_configs.json
    aws dynamodb batch-write-item --request-items file://aws_collab_configs.json
    rm aws_collab_configs.json
fi
