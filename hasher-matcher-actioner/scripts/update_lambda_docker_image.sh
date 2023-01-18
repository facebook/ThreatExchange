#! /bin/bash
# Copyright (c) Meta Platforms, Inc. and affiliates.

set -e

SCRIPT_NAME="$(basename \"$0\")"

if [[ -z "${DOCKER_TAG}" ]]; then
    echo "Please rerun with a DOCKER_TAG set in your local environment" >&2
    echo "e.g., DOCKER_TAG=my_prefix $0" >&2
    exit 1
fi

if [ -d "local-threatexchange" ]; then
    echo "################### WARNING ######################"
    echo "  Using a local copy of threatexchange from the   "
    echo "  local-threatexchange directory to build the "
    echo "  docker image."
    echo " Run './scripts/set_threatexchange_source pypi' if "
    echo " this is not what you want. "
    echo "##################################################"
fi

REPOSITORY_NAME="hma-lambda-dev"

ECS_PASSWORD="$(aws ecr get-login-password --region us-east-1)"
ECR_REPOSITORY_URI="$(aws ecr describe-repositories --repository-names hma-lambda-dev | jq -r '.repositories[0].repositoryUri')"

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "$ECS_PASSWORD" | docker login --username AWS --password-stdin "$ECR_REPOSITORY_URI"
docker build -f Dockerfile -t "$REPOSITORY_NAME" .
docker tag "$REPOSITORY_NAME" "${ECR_REPOSITORY_URI}:${DOCKER_TAG}"
docker push "${ECR_REPOSITORY_URI}:${DOCKER_TAG}"
