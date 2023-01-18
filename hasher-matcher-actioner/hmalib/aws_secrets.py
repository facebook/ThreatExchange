# Copyright (c) Meta Platforms, Inc. and affiliates.
"""
Wrapper functions for reading secrets stored in AWS
"""
import boto3
import base64
import os
import functools
import json
import typing as t
from botocore.errorfactory import ClientError

from hmalib.common.logging import get_logger

logger = get_logger(__name__)


THREAT_EXCHANGE_API_TOKEN_SECRET_NAME = "THREAT_EXCHANGE_API_TOKEN_SECRET_NAME"


class AWSSecrets:
    """
    A class for reading secrets stored in aws. We will be storing everything as
    string, so unless specified, assume everything is a string.

    Except for the older te_api_token and hma_api_tokens secrets, which get
    their SecretIds from environment variables, all other secrets are stored
    with a prefix in their ID. This is to prevent collisions with existing AWS
    Secrets and other instances of HMA (like test, or a new version).
    """

    secrets_client: t.Any

    def __init__(self, prefix: str):
        session = boto3.session.Session()
        self.secrets_client = session.client(service_name="secretsmanager")
        self.prefix = prefix

    def _get_full_secret_id(self, secret_id: str) -> str:
        return f"{self.prefix}{secret_id}"

    def get_secret(self, secret_id: str) -> str:
        """
        Get a secret if it exists. Raises ValueError if it does not.
        """
        try:
            return self._get_str_secret(self._get_full_secret_id(secret_id))
        except ClientError as error:
            if error.response["Error"]["Code"] == "ResourceNotFoundException":
                raise ValueError(f"No secret with secret id: {secret_id}")
            raise error

    def put_secret(self, secret_id: str, secret_value: str):
        """
        Update a secret or create it if does not exist
        """
        try:
            self.secrets_client.put_secret_value(
                SecretId=self._get_full_secret_id(secret_id), SecretString=secret_value
            )
        except ClientError as error:
            if error.response["Error"]["Code"] == "ResourceNotFoundException":
                self.secrets_client.create_secret(
                    Name=self._get_full_secret_id(secret_id), SecretString=secret_value
                )
            else:
                # Can't handle anything else.
                raise error

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
        Deprecated: Do not see any usage. Maybe safe to delete.
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
