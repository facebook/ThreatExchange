# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import os
from hmalib.common import get_logger

logger = get_logger(__name__)

ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]


def lambda_handler(event, _):
    """
    Authorizer for API requesteds
    """
    logger.info(event)
    response = {"isAuthorized": False, "context": {"AuthInfo": "QueryStringTokenCheck"}}

    if event["queryStringParameters"]["access_token"] == ACCESS_TOKEN:
        response["isAuthorized"] = True

    return response
