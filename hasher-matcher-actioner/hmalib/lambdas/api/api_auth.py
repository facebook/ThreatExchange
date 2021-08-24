# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import os
import json
import time
import jwt
import requests
import base64
from jwt.algorithms import RSAAlgorithm

from hmalib.common.logging import get_logger

ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
USER_POOL_URL = os.environ["USER_POOL_URL"]
CLIENT_ID = os.environ["CLIENT_ID"]

keys_url = f"{USER_POOL_URL}/.well-known/jwks.json"

response = requests.get(keys_url)
key_list = json.loads(response.text).get("keys", [])
keys = {key["kid"]: json.dumps(key) for key in key_list}


def is_jwt(token: str) -> bool:
    jwt_split = token.split(".")
    try:
        if len(jwt_split) != 3:
            return False
        header = json.loads(base64.b64decode(jwt_split[0] + "=="))
        if header["alg"] != "RS256":
            return False
    except Exception as e:
        print("INFO: Provisioning Data is not in JWT format\n {0}".format(e))
        return False
    return True


def validate_jwt(token: str):
    logger = get_logger()

    try:
        if not keys:
            logger.error("No JWT public keys found. User auth will always fail.")

        kid = jwt.get_unverified_header(token)["kid"]
        key = keys[kid]

        public_key = RSAAlgorithm.from_jwk(key)

        # Decode does verify_signature
        decoded = jwt.decode(
            token, public_key, algorithms=["RS256"], issuer=USER_POOL_URL
        )

        # Congnito JWT use 'client_id' instead of 'aud' e.g. audience
        if decoded["client_id"] == CLIENT_ID and decoded["token_use"] == "access":
            # Because we don't require username as part of the request,
            # we don't check it beyond making sure it exists.
            username = decoded["username"]
            logger.info(f"User: {username} JWT verified.")
            return {"isAuthorized": True, "context": {"AuthInfo": "JWTTokenCheck"}}

    except Exception as e:
        logger.exception(e)

    return {"isAuthorized": False, "context": {"AuthInfo": "JWTTokenCheck"}}


def validate_access_toke(token: str):
    response = {"isAuthorized": False, "context": {"AuthInfo": "ServiceAccessToken"}}

    if token == ACCESS_TOKEN:
        get_logger().info("Access token approved")
        response["isAuthorized"] = True

    return response


def lambda_handler(event, context):

    token = event["identitySource"][0]

    if is_jwt(token):
        return validate_jwt(token)

    return validate_access_toke(token)


if __name__ == "__main__":
    token = "text_token"
    event = {"identitySource": [token]}
    lambda_handler(event, None)
