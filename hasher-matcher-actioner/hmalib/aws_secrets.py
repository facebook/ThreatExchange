# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
"""
Wrapper functions for reading secrets stored in AWS
"""
import boto3
import base64
import os
import functools
import json
import typing as t

from hmalib.common.logging import get_logger

logger = get_logger(__name__)


THREAT_EXCHANGE_API_TOKEN_SECRET_NAME = "THREAT_EXCHANGE_API_TOKEN_SECRET_NAME"


class AWSSecrets:
    """
    A class for reading secrets stored in aws
    """

    secrets_client: t.Any

    def __init__(self):
        session = boto3.session.Session()
        self.secrets_client = session.client(service_name="secretsmanager")

    def update_te_api_token(self, token: str):
        f"""
        Sets the value of the ThreatExchange API Token in AWS Secrets. Requires
        {THREAT_EXCHANGE_API_TOKEN_SECRET_NAME} be defined in os.environ.

        Raises KeyError if environment variable is not defined.
        """
        secret_name = os.environ[THREAT_EXCHANGE_API_TOKEN_SECRET_NAME]
        self._update_str_secret(secret_name, token)

    def te_api_token(self) -> str:
        f"""
        get the ThreatExchange API Token.
        Requires {THREAT_EXCHANGE_API_TOKEN_SECRET_NAME} be present in environ
        else returns empty string.
        """
        secret_name = os.environ.get(THREAT_EXCHANGE_API_TOKEN_SECRET_NAME)
        if not secret_name:
            logger.warning(
                f"Unable to load {THREAT_EXCHANGE_API_TOKEN_SECRET_NAME} from env"
            )
            return ""
        api_key = self._get_str_secret(secret_name)
        return api_key

    @functools.lru_cache(maxsize=1)
    def hma_api_tokens(self) -> t.List[str]:
        """
        get the set of API tokens for auth of the HMA API.
        Requires HMA_ACCESS_TOKEN_SECRET_NAME be present in environ
        else returns empty list.
        """
        secret_name = os.environ.get("HMA_ACCESS_TOKEN_SECRET_NAME")
        if not secret_name:
            logger.warning("Unable to load HMA_ACCESS_TOKEN_SECRET_NAME from env")
            return []
        access_tokens = self._get_str_secret(secret_name)
        return json.loads(access_tokens)

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

    def _update_str_secret(self, secret_name: str, secret_value: str):
        """
        Update secret_value as the value for secret_name only if it exists.
        """
        self.secrets_client.update_secret(
            SecretId=secret_name, SecretString=secret_value
        )
