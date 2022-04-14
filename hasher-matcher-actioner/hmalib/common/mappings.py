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

from hmalib.common.config import HMAConfig, create_config
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


@dataclass
class ToggleableSignalTypeConfig(HMAConfig):
    signal_type_class: str

    # Allow soft disables.
    enabled: bool = True


@dataclass
class ToggleableContentTypeConfig(HMAConfig):
    content_type_class: str

    # Allow soft disables.
    enabled: bool = True


class HMASignalTypeMapping(SignalTypeMapping):
    """
    An extension of the SignalTypeMapping defined in threatexchange.meta.

    Enhancments:

    1. State is pulled in from dynamodb when __init__ is first called.
    2. Dedicated methods for getting signal and content_type by name. Instead of
       depending on SignalTypeMapping's internal state.
    """

    def __init__(self):
        all_content_types = ToggleableContentTypeConfig.get_all()
        all_signal_types = ToggleableSignalTypeConfig.get_all()

        if len(all_content_types) + len(all_signal_types) == 0:
            # Reasonably sure that we've never set values. So initialize with
            # default values.
            logger.info(
                "First time calling HMASignalTypeMapping.__init__()? Creating default signal and content types.."
            )
            default_content_types, default_signal_types = self._init_configs()
            super().__init__(default_content_types, default_signal_types)
            return

        enabled_content_types = list(
            map(
                lambda c: import_class(c.content_type_class),
                filter(lambda ct: ct.enabled, all_content_types),
            )
        )
        enabled_signal_types = list(
            map(
                lambda c: import_class(c.signal_type_class),
                filter(lambda st: st.enabled, all_signal_types),
            )
        )
        super().__init__(enabled_content_types, enabled_signal_types)

    def _init_configs(
        self,
    ) -> t.Tuple[t.List[t.Type[ContentType]], t.List[t.Type[SignalType]]]:
        """
        Initialize configs such that a subsequent call returns
        DEFAULT_SIGNAL_AND_CONTENT_TYPES.

        WARNING: Not designed for distributed usage. If invoked simultaneously
        by multiple workloads, this may error out because configs.create will be
        called on the same object.
        """
        full_class_name = lambda c: f"{c.__module__}.{c.__name__}"

        content_types = []
        for _type in DEFAULT_SIGNAL_AND_CONTENT_TYPES.content_by_name.values():
            content_config = ToggleableContentTypeConfig(
                name=f"content_type:{full_class_name(_type)}",
                content_type_class=full_class_name(_type),
            )
            create_config(content_config)
            content_types.append(_type)

        signal_types = []
        for _type in DEFAULT_SIGNAL_AND_CONTENT_TYPES.signal_type_by_name.values():
            signal_config = ToggleableSignalTypeConfig(
                name=f"signal_type:{full_class_name(_type)}",
                signal_type_class=full_class_name(_type),
            )
            create_config(signal_config)
            signal_types.append(_type)

        return (content_types, signal_types)

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

    def get_content_Type_enforce(self, name: str) -> t.Type[ContentType]:
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
