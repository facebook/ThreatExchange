# Copyright (c) Meta Platforms, Inc. and affiliates.

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
SECRETS_PREFIX = os.environ["SECRETS_PREFIX"]

# https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html
KEYS_URL = f"{USER_POOL_URL}/.well-known/jwks.json"


logger = get_logger(__name__)


def generatePolicy(principal_id: str, effect: str, method_arn: str):
    # https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-lambda-authorizer-output.html

    # break up method_arn to build resource_arn (we do not have layer auth right now so it is Deny or Allow all)
    tmp = method_arn.split(":")
    api_gw_arn_tmp = tmp[5].split("/")
    aws_account_id = tmp[4]
    rest_api_id = api_gw_arn_tmp[0]
    region = tmp[3]
    stage = api_gw_arn_tmp[1]

    resource_arn = (
        "arn:aws:execute-api:"
        + region
        + ":"
        + aws_account_id
        + ":"
        + rest_api_id
        + "/"
        + stage
        + "/"
        + "*"  # allow ANY Method
        + "/"
        + "*"  # allow any subpath (important for Auth caching reasons)
    )

    statement = {
        "Action": "execute-api:Invoke",
        "Effect": effect,
        "Resource": [resource_arn],
    }

    version = "2012-10-17"  # default
    policy = {
        "principalId": principal_id,
        "policyDocument": {"Version": version, "Statement": [statement]},
    }
    return policy


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
            return True

    except Exception as e:
        logger.exception(e)

    logger.debug("JWT verification failed.")
    return False


# 10 is ~arbitrary: maxsize > 1 because it is possible for their to be more than one
# access token in use that we want to cache, however a large number is unlikely.
@functools.lru_cache(maxsize=10)
def validate_access_token(token: str) -> bool:

    access_tokens = AWSSecrets(prefix=SECRETS_PREFIX).hma_api_tokens()
    if not access_tokens or not token:
        logger.debug("No access tokens found")
        return False

    if token in access_tokens:
        return True
    return False


def validate_jwt_token(token: str) -> bool:
    try:
        # try to decode without any validation just to see if it is a JWT
        jwt.decode(token, algorithms=["RS256"], options={"verify_signature": False})
        return validate_jwt(token)
    except jwt.DecodeError:
        logger.debug("JWT decode failed.")
    return False


def lambda_handler(event, context):
    case_insensitive_headers = {k.lower(): v for k, v in event["headers"].items()}
    token = case_insensitive_headers["authorization"]
    if validate_access_token(token) or validate_jwt_token(token):
        policy = generatePolicy("user", "Allow", event["methodArn"])
        return policy
    else:
        policy = generatePolicy("user", "Deny", event["methodArn"])
        return policy


if __name__ == "__main__":
    token = "text_token"
    event = {
        "headers": {"Authorization": token},
        "methodArn": "arn:aws:execute-api:us-east-1:123456789012:abcdefg123/api/GET/",
    }
    print(lambda_handler(event, None))
