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
import time

import flask

from threatexchange.content_type.content_base import ContentType
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.signal_type.index import SignalTypeIndex
from threatexchange.exchanges.fetch_state import (
    FetchCheckpointBase,
    CollaborationConfigBase,
    FetchedSignalMetadata,
    TUpdateRecordKey,
)
from threatexchange.exchanges.auth import CredentialHelper
from threatexchange.exchanges.signal_exchange_api import (
    TSignalExchangeAPI,
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
    enabled_ratio: float
    signal_type: t.Type[SignalType]

    @property
    def enabled(self) -> bool:
        # TODO do a coin flip here, but also refactor this to do seeding
        return self.enabled_ratio >= 0.0


class ISignalTypeConfigStore(metaclass=abc.ABCMeta):
    """Interface for accessing SignalType configuration"""

    @abc.abstractmethod
    def get_signal_type_configs(self) -> t.Mapping[str, SignalTypeConfig]:
        """Return all installed signal types."""

    @abc.abstractmethod
    def _create_or_update_signal_type_override(
        self, signal_type: str, enabled_ratio: float
    ) -> None:
        """Create or update database entry for a signal type, setting a new value."""

    @t.final
    def create_or_update_signal_type_override(
        self, signal_type: str, enabled_ratio: float
    ) -> None:
        """Update enabled ratio of an installed signal type."""
        installed_signal_types = self.get_signal_type_configs()
        if signal_type not in installed_signal_types:
            raise ValueError(f"Unknown signal type {signal_type}")
        if not (0.0 <= enabled_ratio <= 1.0):
            raise ValueError(
                f"Invalid enabled ratio {enabled_ratio}. Must be in the range 0.0-1.0 inclusive."
            )
        self._create_or_update_signal_type_override(signal_type, enabled_ratio)

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


@dataclass
class SignalTypeIndexBuildCheckpoint:
    """
    A point at which the index has been built up to.

    This feature allows the index to skip a build when nothing has changed,
    which is mostly useful for debugging. Once you have enough ongoing
    changes to the db, the value of eliding builds goes down, and
    a naive implementation could not even store this.

    The key check is the DB's last added hash id, and the total hash count
    """

    # When the most recent item in the bank was added
    # allows for optional fast incremental build for additions
    last_item_timestamp: int
    # What was the id of the last added id to the DB on build
    last_item_id: int
    # What is the total hash db size (to account for removals)
    total_hash_count: int

    @classmethod
    def get_empty(cls):
        """Represents a checkpoint for an empty index / no hashes."""
        return cls(last_item_timestamp=-1, last_item_id=-1, total_hash_count=0)


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
        self,
        signal_type: t.Type[SignalType],
    ) -> t.Optional[SignalTypeIndex[int]]:
        """
        Return the built index for this SignalType.

        For OMM, the indexed values are the ids of BankedContent
        """

    @abc.abstractmethod
    def store_signal_type_index(
        self,
        signal_type: t.Type[SignalType],
        index: SignalTypeIndex,
        checkpoint: SignalTypeIndexBuildCheckpoint,
    ) -> None:
        """
        Persists the signal type index, potentially replacing a previous version.
        """

    @abc.abstractmethod
    def get_last_index_build_checkpoint(
        self, signal_type: t.Type[SignalType]
    ) -> t.Optional[SignalTypeIndexBuildCheckpoint]:
        """
        Returns chekpoint for last index build if it exists
        """


@dataclass
class SignalExchangeAPIConfig:
    """
    Holder for SignalExchangeAPIConfig configuration.
    """

    exchange_cls: TSignalExchangeAPICls
    credentials: t.Optional[CredentialHelper] = None


@dataclass(kw_only=True)
class FetchStatus:
    checkpoint_ts: t.Optional[int]

    running_fetch_start_ts: t.Optional[int]

    last_fetch_complete_ts: t.Optional[int]
    last_fetch_succeeded: t.Optional[bool]
    up_to_date: bool

    fetched_items: int

    @property
    def fetch_in_progress(self) -> bool:
        return self.running_fetch_start_ts is not None

    @classmethod
    def get_default(cls) -> t.Self:
        return cls(
            checkpoint_ts=None,
            running_fetch_start_ts=None,
            last_fetch_complete_ts=None,
            last_fetch_succeeded=None,
            up_to_date=False,
            fetched_items=0,
        )


class ISignalExchangeStore(metaclass=abc.ABCMeta):
    """Interface for accessing SignalExchange configuration"""

    @abc.abstractmethod
    def exchange_type_get_configs(self) -> t.Mapping[str, SignalExchangeAPIConfig]:
        """
        Return all installed SignalExchange types.
        """

    @abc.abstractmethod
    def exchange_type_update(
        self, cfg: SignalExchangeAPIConfig, *, create: bool = False
    ) -> None:
        """
        Create or update the config for exchange API.

        If create is false, if the name doesn't exist it will throw
        If create is true, if the name already exists it will throw
        """

    @abc.abstractmethod
    def exchange_type_delete(self, name: str) -> None:
        """
        Delete collaboration/exchange.

        No exception is thrown if a config with that name doesn't exist
        """

    @abc.abstractmethod
    def exchange_update(
        self, cfg: CollaborationConfigBase, *, create: bool = False
    ) -> None:
        """
        Create or update a collaboration/exchange.

        If create is false, if the name doesn't exist it will throw
        If create is true, if the name already exists it will throw
        """

    @abc.abstractmethod
    def exchange_delete(self, name: str) -> None:
        """
        Delete collaboration/exchange.

        No exception is thrown if a config with that name doesn't exist
        """

    @abc.abstractmethod
    def exchanges_get(self) -> t.Mapping[str, CollaborationConfigBase]:
        """
        Get all collaboration configs.

        Collaboration configs control the syncing of data from external
        sources to banks of labeled content locally.
        """

    def exchange_get(self, name: str) -> t.Optional[CollaborationConfigBase]:
        """Get one collaboration config, if it exists"""
        return self.exchanges_get().get(name)

    @abc.abstractmethod
    def exchange_get_fetch_status(self, name: str) -> FetchStatus:
        """
        Get the last fetch status.
        """

    @abc.abstractmethod
    def exchange_get_fetch_checkpoint(
        self, name: str
    ) -> t.Optional[FetchCheckpointBase]:
        """
        Get the last fetch checkpoint.

        If there is no previous fetch, returns None.
        """

    @abc.abstractmethod
    def exchange_start_fetch(self, collab_name: str) -> None:
        """Record the start of a fetch attempt for this collab"""

    @abc.abstractmethod
    def exchange_complete_fetch(
        self, collab_name: str, *, is_up_to_date: bool, exception: bool
    ) -> None:
        """
        Record that the fetch has completed, as well as how the fetch went.
        """

    @abc.abstractmethod
    def exchange_commit_fetch(
        self,
        collab: CollaborationConfigBase,
        old_checkpoint: t.Optional[FetchCheckpointBase],
        # The merged data from sequential fetches of the API
        dat: t.Dict[str, t.Any],
        # The last checkpoint recieved by the API
        checkpoint: FetchCheckpointBase,
    ) -> None:
        """
        Commit a sequentially fetched set of data from a fetch().

        The old checkpoint can be used in two ways:
            1. As a very weak attempt to prevent stomping old data in the
               case of two process trying to commit at the same time.
            2. If is_stale() is true, the storage can attempt to do something
               smarter than dropping all data and reloading, which can prevent
               the index from "flapping" if all the data is the same.
        """

    @abc.abstractmethod
    def exchange_get_data(
        self,
        collab_name: str,
        key: TUpdateRecordKey,
    ) -> FetchedSignalMetadata:
        """
        Get API-specific collaboration data by key.

        This is only stored if the configuration for the exchange enables it,
        otherwise an exception should be thrown.
        """


@dataclass
class BankConfig:
    # UPPER_WITH_UNDER syntax
    name: str
    # 0.0-1.0 - what percentage of contents should be
    # considered a match? Seeded by target content
    matching_enabled_ratio: float

    @property
    def enabled(self) -> bool:
        return self.matching_enabled_ratio > 0.0


@dataclass
class BankContentConfig:
    """
    Represents all the signals (hashes) for one piece of content.

    When signals come from external sources, or the original content
    has been lost
    """

    ENABLED: t.ClassVar[int] = 1
    DISABLED: t.ClassVar[int] = 0

    # This is what is indexed in the indice and directly returned by
    # lookup
    id: int
    # Disable matching for just one seed content
    # Has some magic values as well:
    #   0 - disabled
    #   1 - enabled
    disable_until_ts: int
    # If this content is originally from a collaboration, includes
    # the name of the collaboration as well as the keys for use with
    # ICollaborationStore.get_collab_data
    collab_metadata: t.Mapping[str, t.Sequence[str]]
    original_media_uri: t.Optional[str]

    bank: BankConfig

    @property
    def enabled(self) -> bool:
        if self.disable_until_ts == 0:
            return False
        if self.disable_until_ts == 1:
            return True
        return self.disable_until_ts <= time.time()


@dataclass
class BankContentIterationItem:
    """
    An item streamed from the datastore for building the index.
    """

    signal_type_name: str
    signal_val: str
    bank_content_id: int
    bank_content_timestamp: int


class IBankStore(metaclass=abc.ABCMeta):
    """
     Interface for maintaining collections of labeled content (aka banks).

     The lifecycle of content is

          Content
             |
           (Hash)
             |
             v
          Signals
             |
        (Add to Bank)
             |
             v
    +-> id: BankContent
    |        |
    |   (Build Index)
    |        |
    |        v
    +--<-- Index <-- Query
    """

    @abc.abstractmethod
    def get_banks(self) -> t.Mapping[str, BankConfig]:
        """Return all bank configs"""

    def get_bank(self, name: str) -> t.Optional[BankConfig]:
        """Return one bank config"""
        return self.get_banks().get(name)

    @abc.abstractmethod
    def bank_update(
        self,
        bank: BankConfig,
        *,
        create: bool = False,
        rename_from: t.Optional[str] = None,
    ) -> None:
        """
        Update a bank config in the backing store.

        If create is false, will throw an exception if not already existing.
        If create is true, will throw an exception if it already exists
        If create is false and you're updating the name, rename_from must be provided
        """

    @abc.abstractmethod
    def bank_delete(self, name: str) -> None:
        """
        Delete a bank entirely.

        If no such bank exists, no exception is thrown.
        """

    # Bank content
    @abc.abstractmethod
    def bank_content_get(self, id: t.Iterable[int]) -> t.Sequence[BankContentConfig]:
        """Get the content config for a bank"""

    @abc.abstractmethod
    def bank_content_update(self, val: BankContentConfig) -> None:
        """Update the content config for a bank"""

    @abc.abstractmethod
    def bank_add_content(
        self,
        bank_name: str,
        content_signals: t.Dict[t.Type[SignalType], str],
        config: t.Optional[BankContentConfig] = None,
    ) -> int:
        """
        Add content (Photo, Video, etc) to a bank, where it can match content.

        Indexing is not instant, there may be a delay before it match APIs can hit it.
        """

    @abc.abstractmethod
    def bank_remove_content(self, bank_name: str, content_id: int) -> None:
        """Remove content from bank by id"""

    @abc.abstractmethod
    def get_current_index_build_target(
        self, signal_type: t.Type[SignalType]
    ) -> SignalTypeIndexBuildCheckpoint:
        """Get information about the total bank size for skipping an index build"""

    @abc.abstractmethod
    def bank_yield_content(
        self, signal_type: t.Optional[t.Type[SignalType]] = None, batch_size: int = 100
    ) -> t.Iterator[BankContentIterationItem]:
        """
        Yield the entire content of the bank in batches.

        If a signal type is provided, will yield signals of that type if
        they are available for that content.
        """


class IUnifiedStore(
    IContentTypeConfigStore,
    ISignalTypeConfigStore,
    ISignalExchangeStore,
    ISignalTypeIndexStore,
    IBankStore,
    metaclass=abc.ABCMeta,
):
    """
    All the store classes combined into one interfaces.

    This is probably the most common way to use this, especially early on
    in development - the option to pass them more narrowly is helpful
    mostly for typing.
    """

    def init_flask(cls, app: flask.Flask) -> None:
        """
        Make any flask-specific initialization for this storage implementation

        This serves as the normal constructor when used with OMM, which allows
        you to write __init__ how is most useful to your implementation for
        testing.
        """
        return
