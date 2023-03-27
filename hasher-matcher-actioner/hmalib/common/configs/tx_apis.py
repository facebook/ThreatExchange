# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
DynamoDB backed SignalExchangeAPI objects.
"""

from dataclasses import dataclass
import typing as t
from enum import Enum

from botocore.exceptions import ClientError
from threatexchange.exchanges.signal_exchange_api import SignalExchangeAPI
from threatexchange.exchanges.impl.file_api import LocalFileSignalExchangeAPI

from hmalib.common.config import HMAConfig, create_config, update_config
from hmalib.common.logging import get_logger
from hmalib.common.mappings import full_class_name, import_class

logger = get_logger(__name__)


@dataclass
class ToggleableSignalExchangeAPIConfig(HMAConfig):
    signal_exchange_api_class: str

    # Allow soft disables
    enabled: bool = True

    @staticmethod
    def get_name_from_type(signal_exchange_api: t.Type[SignalExchangeAPI]) -> str:
        return f"signal_exchange_api:{full_class_name(signal_exchange_api)}"

    def to_concrete_class(self) -> t.Type[SignalExchangeAPI]:
        return import_class(self.signal_exchange_api_class)

    @classmethod
    def get_all(
        cls: t.Type["ToggleableSignalExchangeAPIConfig"],
    ) -> t.List["ToggleableSignalExchangeAPIConfig"]:
        return [
            api
            for api in super(ToggleableSignalExchangeAPIConfig, cls).get_all()
            # Do not want to handle local files without supporting s3 uploads
            # for those files..
            if api.to_concrete_class() is not LocalFileSignalExchangeAPI
        ]

    def get_credential_name(self):
        """
        What name would we store the secret under. Only useful if signal
        exchange class subclasses auth.SignalExchangeWithAuth.
        """
        return f"{self.signal_exchange_api_class}/api_credentials"


class AddSignalExchangeAPIResult(Enum):
    FAILED = 1
    ALREADY_EXISTS = 2
    ADDED = 3


def add_signal_exchange_api(
    klass: str,
) -> AddSignalExchangeAPIResult:
    try:
        cls = import_class(klass)
    except (ModuleNotFoundError, AttributeError) as e:
        logger.warning("Failed to add SignalExchangeAPI with class: %s", klass)
        logger.exception(e)
        return AddSignalExchangeAPIResult.FAILED

    try:
        create_config(
            ToggleableSignalExchangeAPIConfig(
                name=ToggleableSignalExchangeAPIConfig.get_name_from_type(cls),
                signal_exchange_api_class=full_class_name(cls),
                enabled=True,
            )
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            logger.warning(
                "Attempted to add SignalExchangeAPI with class: %s, but it already exists.",
                klass,
            )
            return AddSignalExchangeAPIResult.ALREADY_EXISTS
        else:
            raise e

    return AddSignalExchangeAPIResult.ADDED


class SignalExchangeAPIStatus(Enum):
    ENABLED = 1
    DISABLED = 2


class UpdateSignalExchangeAPIStatusResult(Enum):
    DISABLED = 1
    ENABLED = 2
    FAILED = 3


def set_status_signal_exchange_api(
    klass: str, status: SignalExchangeAPIStatus
) -> UpdateSignalExchangeAPIStatusResult:
    """
    Convenience method. Will fail if klass does not translate to an actual
    SignalExchangeAPI.
    """
    try:
        cls = import_class(klass)
    except (ModuleNotFoundError, AttributeError) as ex:
        logger.error("Can't load class to disable SignalExchangeAPI: %s", klass)
        logger.exception(ex)
        return UpdateSignalExchangeAPIStatusResult.FAILED

    config = ToggleableSignalExchangeAPIConfig.get(
        ToggleableSignalExchangeAPIConfig.get_name_from_type(cls)
    )

    if not config:
        return UpdateSignalExchangeAPIStatusResult.FAILED

    config = t.cast(ToggleableSignalExchangeAPIConfig, config)
    config.enabled = status == SignalExchangeAPIStatus.ENABLED
    update_config(config)

    return (
        status
        and UpdateSignalExchangeAPIStatusResult.ENABLED
        or UpdateSignalExchangeAPIStatusResult.DISABLED
    )
