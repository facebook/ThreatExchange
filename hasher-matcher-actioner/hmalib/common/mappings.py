# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

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
from threatexchange.meta import (
    FunctionalityMapping,
    SignalTypeMapping,
    FetcherMapping,
    CollaborationConfigStoreBase,
)
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.fetcher.fetch_api import SignalExchangeAPI
from threatexchange.fetcher.apis.fb_threatexchange_api import (
    FBThreatExchangeSignalExchangeAPI,
)
from threatexchange.content_type.photo import PhotoContent
from threatexchange.content_type.video import VideoContent
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.pdq import PdqSignal

from hmalib.common.config import (
    HMAConfig,
    create_config,
    create_or_update_config,
    update_config,
)
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


"""
Reverses import_class. Will create a module.ClassName style string that can
be imported using import_class.
"""


def full_class_name(klass) -> str:
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


class HMASignalTypeMapping(SignalTypeMapping):
    """
    An extension of the SignalTypeMapping defined in threatexchange.meta.

    Enhancements:

    1. State is pulled in from dynamodb when __init__ is first called.
    2. Dedicated methods for getting signal and content_type by name. Instead of
       depending on SignalTypeMapping's internal state.
    """

    @classmethod
    def get_from_config_or_default(cls) -> "HMASignalTypeMapping":
        """
        Pull configs from HMAConfigs if available. If not, use defaults.
        """
        all_content_types = ToggleableContentTypeConfig.get_all()
        all_signal_types = ToggleableSignalTypeConfig.get_all()

        if len(all_content_types) + len(all_signal_types) == 0:
            # We have never written content or signal types to database, so use
            # default values instead.
            (
                all_content_types,
                all_signal_types,
            ) = cls._get_default_configs()

        enabled_content_types = [
            import_class(ct.content_type_class)
            for ct in all_content_types
            if ct.enabled
        ]
        enabled_signal_types = [
            import_class(st.signal_type_class) for st in all_signal_types if st.enabled
        ]

        return HMASignalTypeMapping(enabled_content_types, enabled_signal_types)

    @classmethod
    def _get_default_configs(
        cls,
    ) -> t.Tuple[
        t.List[ToggleableContentTypeConfig], t.List[ToggleableSignalTypeConfig]
    ]:
        """
        Return default ToggleableContentTypeConfigs and
        ToggleableSignalTypeConfigs. These are not guaranteed to be in the
        config database.
        """
        content_type_configs = []
        for _type in DEFAULT_SIGNAL_AND_CONTENT_TYPES.content_by_name.values():
            content_config = ToggleableContentTypeConfig(
                name=ToggleableContentTypeConfig.get_name_from_type(_type),
                content_type_class=full_class_name(_type),
            )
            content_type_configs.append(content_config)

        signal_type_configs = []
        for _type in DEFAULT_SIGNAL_AND_CONTENT_TYPES.signal_type_by_name.values():
            signal_config = ToggleableSignalTypeConfig(
                name=ToggleableSignalTypeConfig.get_name_from_type(_type),
                signal_type_class=full_class_name(_type),
            )
            signal_type_configs.append(signal_config)

        return (content_type_configs, signal_type_configs)

    def write_as_configs(self):
        """
        Write current state to dynamodb. This will create or update HMAConfigs
        so that subsequent calls to get_from_config_or_default() return current
        state.

        Note: this will also disable signal and content types that are not part
        of current state.
        """
        self._write_content_types_as_configs()
        self._write_signal_types_as_configs()

    def _write_content_types_as_configs(self):
        self_enabled_ct_classes = [
            full_class_name(ct) for ct in self.content_by_name.values()
        ]

        all_ct_configs = ToggleableContentTypeConfig.get_all()
        for ct_config in all_ct_configs:
            if ct_config.content_type_class not in self_enabled_ct_classes:
                # Disable content types that are not currently part of self.content_by_name
                ct_config.enabled = False
                update_config(ct_config)
            else:
                # Force enable content types that are part of self.content_by_name
                ct_config.enabled = True
                update_config(ct_config)

        for ct_class in self.content_by_name.values():
            # Create or update config for each enabled ct class.
            ct_config = ToggleableContentTypeConfig(
                name=ToggleableContentTypeConfig.get_name_from_type(ct_class),
                content_type_class=full_class_name(ct_class),
            )
            create_or_update_config(ct_config)

    def _write_signal_types_as_configs(self):
        self_enabled_st_classes = [
            full_class_name(st) for st in self.signal_type_by_name.values()
        ]

        all_st_configs = ToggleableSignalTypeConfig.get_all()
        for st_config in all_st_configs:
            if st_config.content_type_class not in self_enabled_st_classes:
                # Disable content types that are not currently part of self.content_by_name
                st_config.enabled = False
                update_config(st_config)
            else:
                # Force enable content types that are part of self.content_by_name
                st_config.enabled = True
                update_config(st_config)

        for st_class in self.signal_type_by_name.values():
            # Create or update config for each enabled st class.
            st_config = ToggleableSignalTypeConfig(
                name=ToggleableSignalTypeConfig.get_name_from_type(st_class),
                signal_type_class=full_class_name(st_class),
            )
            create_or_update_config(st_config)

    def get_signal_type(self, name: str) -> t.Optional[t.Type[SignalType]]:
        return self.signal_type_by_name.get(name, None)

    def get_content_type(self, name: str) -> t.Optional[t.Type[ContentType]]:
        return self.content_by_name.get(name, None)

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


@dataclass
class HMAFunctionalityMapping(FunctionalityMapping):
    """
    Overrides signal_and_content on FunctionalityMapping so it is of type
    HMAFunctionalityMapping.
    """

    signal_and_content: HMASignalTypeMapping

    # mypy has this weird behaviour where not overriding all fields leads to a
    # "Too many arguments error". Either type:ignore at __init__ callsites or
    # re-define them here.
    fetcher: FetcherMapping
    collabs: CollaborationConfigStoreBase


def get_pytx_functionality_mapping() -> HMAFunctionalityMapping:
    """
    Call from HMA entrypoints. Ensure HMAConfig.initialize() has already been
    called.
    """
    fetchers: t.List[SignalExchangeAPI] = []

    threatexchange_api_token = AWSSecrets().te_api_token()
    if not threatexchange_api_token in (None, ""):
        fetchers.append(
            FBThreatExchangeSignalExchangeAPI(threatexchange_api_token),
        )

    return HMAFunctionalityMapping(
        HMASignalTypeMapping(),
        FetcherMapping(fetchers=fetchers),
        None,
    )
