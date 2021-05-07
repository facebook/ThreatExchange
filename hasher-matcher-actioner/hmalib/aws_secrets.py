# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
"""
Wrapper functions for reading secrets stored in AWS
"""
import boto3
import base64
import os
import typing as t


class AWSSecrets:
    """
    A class for reading secrets stored in aws
    """

    secrets_client: t.Any

    def __init__(self):
        session = boto3.session.Session()
        self.secrets_client = session.client(service_name="secretsmanager")

    def te_api_key(self) -> str:
        """
        get the ThreatExchange API Key
        """
        secret_name = os.environ["THREAT_EXCHANGE_API_TOKEN_SECRET_NAME"]
        api_key = self._get_str_secret(secret_name)
        return api_key

    def _get_bin_secret(self, secret_name: str) -> bytes:
        """
        For secerts stored in AWS Secrets Manager as binary
        """
        response = self._get_secret_value_response(secret_name)
        decoded_binary_secret = base64.b64decode(
            self._get_secret_value_response("SecretBinary")
        )
        return decoded_binary_secret

    def _get_str_secret(self, secret_name: str) -> str:
        """
        For secerts stored in AWS Secrets Manager as strings
        """
        response = self._get_secret_value_response(secret_name)
        str_response = response["SecretString"]
        return str_response

    def _get_secret_value_response(self, secret_name: str):
        get_secret_value_response = self.secrets_client.get_secret_value(
            SecretId=secret_name
        )
        return get_secret_value_response
