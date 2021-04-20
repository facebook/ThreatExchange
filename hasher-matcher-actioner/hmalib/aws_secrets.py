# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
"""
Wrapper functions for reading secrets stored in AWS
"""

import boto3
import base64
import os
import typing as t

session = boto3.session.Session()
secrets_client = session.client(service_name="secretsmanager", region_name="us-east-1")


class AWSSecrets:
    """
    A class for reading secrets stored in aws
    """

    @classmethod
    def te_api_key(self) -> str:
        """
        get the ThreatExchange API Key
        """
        secret_name = os.environ["THREAT_EXCHANGE_API_TOKEN_SECRET_NAME"]
        api_key = get_str_secret(secret_name)
        return api_key


def get_bin_secret(secret_name: str) -> bytes:
    """
    For secerts stored in AWS Secrets Manager as binary
    """
    response = get_secret_value_response(secret_name)
    decoded_binary_secret = base64.b64decode(get_secret_value_response("SecretBinary"))
    return decoded_binary_secret


def get_str_secret(secret_name: str) -> str:
    """
    For secerts stored in AWS Secrets Manager as strings
    """
    response = get_secret_value_response(secret_name)
    str_response = response["SecretString"]
    return str_response


def get_secret_value_response(secret_name: str):
    get_secret_value_response = secrets_client.get_secret_value(SecretId=secret_name)
    return get_secret_value_response
