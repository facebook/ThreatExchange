# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import logging
import os

ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]

def get_logger():
    """This pattern prevents creates implicitly creating a root logger by creating the sub-logger named __name__"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    return logger

def lambda_handler(event, _):
    """
    Authorizer for API requesteds
    """
    logger = get_logger()
    logger.info(event)
    response = {"isAuthorized": False, "context": {"AuthInfo": "QueryStringTokenCheck"}}

    if event["queryStringParameters"]["access_token"] == ACCESS_TOKEN:
        response["isAuthorized"] = True

    return response
