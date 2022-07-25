# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
DynamoDB backed SignalExchangeAPI objects.
"""

from dataclasses import dataclass
import typing as t
from enum import Enum

from botocore.exceptions import ClientError
from jinja2 import ModuleLoader
from threatexchange.exchanges.signal_exchange_api import SignalExchangeAPI

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
    except ClientError:
        logger.warning(
            "Attempted to add SignalExchangeAPI with class: %s, but it already exists.",
            klass,
        )
        return AddSignalExchangeAPIResult.ALREADY_EXISTS

    return AddSignalExchangeAPIResult.ADDED


class DisableSignalExchangeAPIResult(Enum):
    DISABLED = 1
    FAILED = 2


def disable_signal_exchange_api(
    klass: str,
) -> DisableSignalExchangeAPIResult:
    """
    Convenience method. Will fail if klass does not translate to an actual
    SignalExchangeAPI.
    """
    try:
        cls = import_class(klass)
    except (ModuleNotFoundError, AttributeError) as ex:
        logger.error("Can't load class to disable SignalExchangeAPI: %s", klass)
        logger.exception(ex)
        return DisableSignalExchangeAPIResult.FAILED

    config = ToggleableSignalExchangeAPIConfig.get(
        ToggleableSignalExchangeAPIConfig.get_name_from_type(cls)
    )

    if not config:
        return DisableSignalExchangeAPIResult.FAILED

    config = t.cast(ToggleableSignalExchangeAPIConfig, config)
    config.enabled = False
    update_config(config)
    return DisableSignalExchangeAPIResult.DISABLED
