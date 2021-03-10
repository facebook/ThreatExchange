# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import logging
import os

import boto3
import json


logger = logging.getLogger()
logger.setLevel(logging.INFO)

# s3_client = boto3.client("s3")
# dynamodb  = boto3.resource("dynamodb")

# DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]


def lambda_handler(event, context):
    """
    Status of delpoyed HMA 
    """
    # logger.info("Received event: " + json.dumps(event, indent=2))

    return {
        'statusCode': '200',
        'body': 'Hello World, HMA',
        'headers': {
            'Content-Type': 'application/json',
        },
    }