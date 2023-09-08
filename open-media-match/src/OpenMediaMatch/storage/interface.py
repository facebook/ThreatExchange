# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Abstraction layer for fetching information needed to run OMM.

To try and separate concerns for extension, this file provides
access to all the persistent data needed to run OMM. In the 
default implementation, we have a unified implementation that 
implements all interfaces, but different implementations may
prefer to store different data in different places.

For implementations, see storage.mocked.MockedStore, which provides
plausable defaults for all of these interfaces, useful for testing,
or storage.default.DefaultOMMStore, which uses a combination of
static configuration and postgres. 
"""

import abc
from dataclasses import dataclass
import typing as t
from threatexchange.content_type.content_base import ContentType
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.exchanges.signal_exchange_api import (
    TSignalExchangeAPICls,
)


@dataclass
class ContentTypeConfig:
    """
    Holder for ContentType configuration.
    """

    # Content types that are not enabled should not be used in hashing/matching
    enabled: bool
    content_type: ContentType


class IContentTypeConfigStore(metaclass=abc.ABCMeta):
    """Interface for accessing ContentType configuration"""

    @abc.abstractmethod
    def get_content_type_configs(self) -> t.Mapping[str, ContentTypeConfig]:
        """
        Return all installed content types.
        """


@dataclass
class SignalTypeConfig:
    """
    Holder for SignalType configuration
    """

    # Signal types that are not enabled should not be used in hashing/matching
    enabled: bool
    signal_type: SignalType


class ISignalTypeConfigStore(metaclass=abc.ABCMeta):
    """Interface for accessing SignalType configuration"""

    @abc.abstractmethod
    def get_signal_type_configs(self) -> t.Mapping[str, SignalTypeConfig]:
        """Return all installed signal types."""

    @t.final
    def get_enabled_signal_types(self) -> t.Mapping[str, SignalType]:
        """Helper shortcut for getting only enabled SignalTypes"""
        return {
            k: v.signal_type
            for k, v in self.get_signal_type_configs().items()
            if v.enabled
        }

    @t.final
    def get_enabled_signal_types_for_content_type(
        self, content_type: ContentType
    ) -> t.Mapping[str, SignalType]:
        """Helper shortcut for getting enabled types for a piece of content"""
        return {
            k: v.signal_type
            for k, v in self.get_signal_type_configs().items()
            if v.enabled and content_type in v.signal_type.get_content_types()
        }


class ISignalExchangeConfigStore(metaclass=abc.ABCMeta):
    """Interface for accessing SignalExchange configuration"""

    @abc.abstractmethod
    def get_exchange_type_configs(self) -> t.Mapping[str, TSignalExchangeAPICls]:
        """
        Return all installed SignalExchange types.
        """


# TODO - index, collaborations, banks, OMM-specific


class IUnifiedStore(
    IContentTypeConfigStore,
    ISignalTypeConfigStore,
    ISignalExchangeConfigStore,
    metaclass=abc.ABCMeta,
):
    """
    All the store classes combined into one interfaces.

    This is probably the most common way to use this, especially early on
    in development - the option to pass them more narrowly is helpful
    mostly for typing.
    """
