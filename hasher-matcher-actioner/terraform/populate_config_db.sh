#!/usr/bin/env bash
cat collabs.json | jq "{ $1 : . }" > aws_collab_configs.json
aws dynamodb batch-write-item --request-items file://aws_collab_configs.json
rm aws_collab_configs.json
