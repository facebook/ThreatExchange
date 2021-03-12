# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import boto3
import base64
import typing as t
import os
import ast
from botocore.exceptions import ClientError

from threatexchange.api import ThreatExchangeAPI

AWS_REGION = os.environ["AWS_REGION"]

class AWSSecrets():
    """
    A class for reading secrets stored in aws for interacting with ThreatExchange
    """
    def te_api_data(self) -> "ThreatExchangeAPI" :
        secret_name = "threatexchange/api_keys"
        secret_str = get_str_secret(secret_name)
        return ThreatExchangeAPI(secret_str)

def get_bin_secret(secret_name: str) -> t.BinaryIO:
    response = get_secret_value_response(secret_name)
    assert response and 'SecretBinary' in response
    decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
    return decoded_binary_secret

def get_str_secret(secret_name: str) -> str:
    response = get_secret_value_response(secret_name)
    assert response and 'SecretString' in response
    str_response = response['SecretString']
    dict_response = ast.literal_eval(str_response)
    if type(dict_response) is dict:
        return dict_response["default"]
    return str_response

def get_secret_value_response(secret_name: str):

    # Create a Secrets Manager client
    session = boto3.session.Session()
    secrets_client = session.client(
        service_name='secretsmanager',
        region_name=AWS_REGION
    )
    get_secret_value_response = secrets_client.get_secret_value(
            SecretId=secret_name
        )
    return get_secret_value_response
