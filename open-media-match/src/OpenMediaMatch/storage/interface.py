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
from threatexchange.signal_type.index import SignalTypeIndex
from threatexchange.exchanges.fetch_state import (
    FetchCheckpointBase,
    CollaborationConfigBase,
)
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
    content_type: t.Type[ContentType]


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
    signal_type: t.Type[SignalType]


class ISignalTypeConfigStore(metaclass=abc.ABCMeta):
    """Interface for accessing SignalType configuration"""

    @abc.abstractmethod
    def get_signal_type_configs(self) -> t.Mapping[str, SignalTypeConfig]:
        """Return all installed signal types."""

    @t.final
    def get_enabled_signal_types(self) -> t.Mapping[str, t.Type[SignalType]]:
        """Helper shortcut for getting only enabled SignalTypes"""
        return {
            k: v.signal_type
            for k, v in self.get_signal_type_configs().items()
            if v.enabled
        }

    @t.final
    def get_enabled_signal_types_for_content_type(
        self, content_type: t.Type[ContentType]
    ) -> t.Mapping[str, t.Type[SignalType]]:
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


class ISignalTypeIndexStore(metaclass=abc.ABCMeta):
    """
    Interface for accessing index objects.

    In the SignalType interfaces, SignalTypeIndex is a large object that
    contains all the information needed to match content known to the system.

    This means that the index size is ultimately limited by available memory.
    Extensions of OMM looking to solve this scaling problem may need to redesign
    the bank -> indexing -> index flow, shard the index, or other tricks.

    This approach provides a simple backup approach that will work with any
    properly implemented SignalType.
    """

    @abc.abstractmethod
    def get_signal_type_index(
        self, signal_type: t.Type[SignalType]
    ) -> t.Optional[SignalTypeIndex[int]]:
        """
        Return the built index for this SignalType.

        For OMM, the indexed values are BankedIDs
        """


class ICollaborationStore(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_collaborations(self) -> t.Dict[str, CollaborationConfigBase]:
        """
        Get all collaboration configs.

        Collaboration configs control the syncing of data from external
        sources to banks of labeled content locally.
        """

    @abc.abstractmethod
    def get_collab_fetch_checkpoint(
        self, collab: CollaborationConfigBase
    ) -> t.Optional[FetchCheckpointBase]:
        """
        Get the last saved checkpoint for the fetch of this collaboration.

        If there is no previous fetch, returns None, indicating the fetch
        should start from the beginning.
        """

    @abc.abstractmethod
    def commit_collab_fetch_data(
        self,
        collab: CollaborationConfigBase,
        dat: t.Dict[str, t.Any],
        checkpoint: FetchCheckpointBase,
    ):
        """
        Commit a sequentially fetched set of data from a fetch().

        Advances the checkpoint if it's different than the previous one.
        """

    @abc.abstractmethod
    def get_collab_data(
        self,
        collab_name: str,
        key: str,
        checkpoint: FetchCheckpointBase,
    ) -> t.Any:
        """
        Get API-specific collaboration data by key.
        """


# TODO - banks


class IUnifiedStore(
    IContentTypeConfigStore,
    ISignalTypeConfigStore,
    ISignalExchangeConfigStore,
    ISignalTypeIndexStore,
    ICollaborationStore,
    metaclass=abc.ABCMeta,
):
    """
    All the store classes combined into one interfaces.

    This is probably the most common way to use this, especially early on
    in development - the option to pass them more narrowly is helpful
    mostly for typing.
    """
