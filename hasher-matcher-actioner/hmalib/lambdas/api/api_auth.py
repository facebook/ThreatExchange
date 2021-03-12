# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)


ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]


def lambda_handler(event, context):
    """
    authorizer for API requesteds
    """
    logger.info(event)
    logger.info(context)
    response = {"isAuthorized": False, "context": {"AuthInfo": "Customer1"}}

    if event["queryStringParameters"]["access_token"] == ACCESS_TOKEN:
        response["isAuthorized"] = True

    return response
