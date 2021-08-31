# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import os
import json
import time
import jwt
import requests
import base64
import functools
from jwt.algorithms import RSAAlgorithm

from hmalib.aws_secrets import AWSSecrets
from hmalib.common.logging import get_logger

USER_POOL_URL = os.environ["USER_POOL_URL"]
CLIENT_ID = os.environ["CLIENT_ID"]

# https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html
KEYS_URL = f"{USER_POOL_URL}/.well-known/jwks.json"


logger = get_logger(__name__)


@functools.lru_cache(maxsize=1)
def _get_public_keys():
    response = requests.get(KEYS_URL)
    key_list = json.loads(response.text).get("keys", [])
    return {key["kid"]: RSAAlgorithm.from_jwk(json.dumps(key)) for key in key_list}


def validate_jwt(token: str):
    keys = _get_public_keys()
    try:
        if not keys:
            logger.error("No JWT public keys found. User auth will always fail.")

        kid = jwt.get_unverified_header(token)["kid"]
        key = keys[kid]

        # Decode does verify_signature
        decoded = jwt.decode(token, key, algorithms=["RS256"], issuer=USER_POOL_URL)

        # Congnito JWT use 'client_id' instead of 'aud' e.g. audience
        if decoded["client_id"] == CLIENT_ID and decoded["token_use"] == "access":
            # Because we don't require username as part of the request,
            # we don't check it beyond making sure it exists.
            username = decoded["username"]
            logger.debug(f"User: {username} JWT verified.")
            return {"isAuthorized": True, "context": {"AuthInfo": "JWTTokenCheck"}}

    except Exception as e:
        logger.exception(e)

    logger.debug("JWT verification failed.")
    return {"isAuthorized": False, "context": {"AuthInfo": "JWTTokenCheck"}}


def validate_access_token(token: str):
    response = {"isAuthorized": False, "context": {"AuthInfo": "ServiceAccessToken"}}

    access_tokens = AWSSecrets().hma_api_tokens()
    if not access_tokens or not token:
        logger.debug("Rejected empty values")
        return response

    if token in access_tokens:
        logger.debug("Access token approved")
        response["isAuthorized"] = True

    return response


def lambda_handler(event, context):

    token = event["identitySource"][0]

    try:
        # try to decode without any validation just to see if it is a JWT
        jwt.decode(token, algorithms=["RS256"], options={"verify_signature": False})
        return validate_jwt(token)
    except jwt.DecodeError:
        # Does not appear to be a JWT, attempt alternative auth check(s)
        return validate_access_token(token)


if __name__ == "__main__":
    token = "text_token"
    event = {"identitySource": [token]}
    lambda_handler(event, None)
