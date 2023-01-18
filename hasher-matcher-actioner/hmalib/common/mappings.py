# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Configure components of the threatexchange library here.

The get_pytx_functionality_mapping() will be called from almost all entrypoints.
Entrypoints usually, are the modules where a lambda_handler is defined.

Everything that is configurable from threatexchange.meta is stored in dynamodb.
This module also exposes mechanisms to create/edit/delete those configurables. 
"""

from dataclasses import dataclass, field
import importlib
import typing as t
from numpy import append

from threatexchange.content_type.content_base import ContentType
from threatexchange.interface_validation import (
    FunctionalityMapping,
    SignalExchangeAPIMapping,
    SignalTypeMapping,
    SignalExchangeAPIMapping,
    CollaborationConfigStoreBase,
)
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.exchanges.signal_exchange_api import SignalExchangeAPI
from threatexchange.exchanges.impl.fb_threatexchange_api import (
    FBThreatExchangeSignalExchangeAPI,
)
from threatexchange.content_type.photo import PhotoContent
from threatexchange.content_type.video import VideoContent
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.pdq import PdqSignal

from hmalib.common.config import HMAConfig
from hmalib.common.logging import get_logger
from hmalib.aws_secrets import AWSSecrets

# Used if this is the first time HMA is being booted. TODO: Should this be
# configurable before boot?
DEFAULT_SIGNAL_AND_CONTENT_TYPES = SignalTypeMapping(
    content_types=[PhotoContent, VideoContent], signal_types=[VideoMD5Signal, PdqSignal]
)

logger = get_logger(__name__)


def import_class(full_class_name) -> t.Type:
    module_name, klass = full_class_name.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, klass)


def full_class_name(klass) -> str:
    """
    Reverses import_class. Will create a module.ClassName style string that can
    be imported using import_class.
    """
    return f"{klass.__module__}.{klass.__name__}"


@dataclass
class ToggleableSignalTypeConfig(HMAConfig):
    signal_type_class: str

    # Allow soft disables.
    enabled: bool = True

    @staticmethod
    def get_name_from_type(signal_type: t.Type[SignalType]) -> str:
        return f"signal_type:{full_class_name(signal_type)}"


@dataclass
class ToggleableContentTypeConfig(HMAConfig):
    content_type_class: str

    # Allow soft disables.
    enabled: bool = True

    @staticmethod
    def get_name_from_type(content_type: t.Type[ContentType]) -> str:
        return f"content_type:{full_class_name(content_type)}"


class HMASignalTypeMapping:
    """
    Contains signal and content types that will be made available to HMA
    components.

    1. State is pulled in from dynamodb when __init__ is first called.
    2. Dedicated methods for getting signal and content_type by name. Instead of
       depending on SignalTypeMapping's internal state.
    """

    def __init__(
        self,
        content_types: t.List[t.Type[ContentType]],
        signal_types: t.List[t.Type[SignalType]],
    ):
        self._internal_pytx_obj = SignalTypeMapping(content_types, signal_types)

    @classmethod
    def get_from_config(cls) -> "HMASignalTypeMapping":
        """
        Pull configs from HMAConfigs.
        """
        all_content_types = ToggleableContentTypeConfig.get_all()
        all_signal_types = ToggleableSignalTypeConfig.get_all()

        enabled_content_types = [
            import_class(ct.content_type_class)
            for ct in all_content_types
            if ct.enabled
        ]
        enabled_signal_types = [
            import_class(st.signal_type_class) for st in all_signal_types if st.enabled
        ]

        return HMASignalTypeMapping(enabled_content_types, enabled_signal_types)

    @property
    def signal_types(self) -> t.List[t.Type[SignalType]]:
        return self._internal_pytx_obj.signal_type_by_name.values()

    def get_signal_type(self, name: str) -> t.Optional[t.Type[SignalType]]:
        return self._internal_pytx_obj.signal_type_by_name.get(name, None)

    def get_content_type(self, name: str) -> t.Optional[t.Type[ContentType]]:
        return self._internal_pytx_obj.content_by_name.get(name, None)

    def get_signal_type_enforce(self, name: str) -> t.Type[SignalType]:
        """
        Like get_signal_type, but errors out instead of returning None.
        """
        signal_type = self.get_signal_type(name)
        if signal_type is None:
            raise ValueError(
                f"SignalType: '{name}' could not be resolved to a configured SignalType."
            )

        return signal_type

    def get_content_type_enforce(self, name: str) -> t.Type[ContentType]:
        """
        Like get_content_type, but errors out instead of returning None.
        """
        content_type = self.get_content_type(name)
        if content_type is None:
            raise ValueError(
                f"ContentType: '{name}' could not be resolved to a configured ContentType."
            )

        return content_type

    def get_supported_signal_types_for_content(
        self, content: t.Type[ContentType]
    ) -> t.List[t.Type[SignalType]]:
        """
        Returns a list of signal_types for a content.

        Merely proxies the call to the underlying python-threatexchange object.
        """
        return self._internal_pytx_obj.get_supported_signal_types_for_content(content)


@dataclass
class HMAFunctionalityMapping:
    """
    Accessor for signal_and_content types. Among signal_and_content types,
    fetchers and collab configs, only signal_and_content_types appear 'static'
    enough to require a convenience accessor.

    It is used in a bunch of places.
    """

    signal_and_content: HMASignalTypeMapping


def get_pytx_functionality_mapping() -> HMAFunctionalityMapping:
    """
    Call from HMA entrypoints. Ensure HMAConfig.initialize() has already been
    called.
    """
    return HMAFunctionalityMapping(
        HMASignalTypeMapping.get_from_config(),
    )
