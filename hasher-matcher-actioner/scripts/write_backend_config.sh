#! /bin/bash
# Copyright (c) Meta Platforms, Inc. and affiliates.

[[ ! -z "$TF_STATE_S3_BUCKET" ]] && s3_bucket="$TF_STATE_S3_BUCKET" || s3_bucket="threatexchange-tf-state"
[[ ! -z "$TF_STATE_S3_KEY" ]] && s3_key="$TF_STATE_S3_KEY" || s3_key="state\/hasher-matcher-actioner-$(whoami).tfstate"
[[ ! -z "$TF_STATE_AWS_REGION" ]] && aws_region="$TF_STATE_AWS_REGION" || aws_region="us-east-1"
[[ ! -z "$TF_STATE_LOCKING_TABLE" ]] && table_name="$TF_STATE_LOCKING_TABLE" || table_name="terraform-state-locking"

sed \
    -e "s/# TERRAFORM_STATE_S3_BUCKET/\"${s3_bucket}\"/" \
    -e "s/# TERRAFORM_STATE_KEY/\"${s3_key}\"/" \
    -e "s/# TERRAFORM_BUCKET_REGION/\"${aws_region}\"/" \
    -e "s/# TERRAFORM_STATE_LOCKING_TABLE/\"${table_name}\"/" \
    terraform/backend.tf.example
