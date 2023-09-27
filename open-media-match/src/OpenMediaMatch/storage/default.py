# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
The default store for accessing persistent data on OMM.
"""

import typing as t

from threatexchange.exchanges.signal_exchange_api import TSignalExchangeAPICls
from threatexchange.signal_type.index import SignalTypeIndex
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.exchanges.fetch_state import (
    FetchCheckpointBase,
    CollaborationConfigBase,
)


from OpenMediaMatch.storage import interface
from OpenMediaMatch.storage.mocked import MockedUnifiedStore
from OpenMediaMatch.storage.interface import SignalTypeConfig


class DefaultOMMStore(interface.IUnifiedStore):
    """
    The default store for accessing persistent data on OMM.

    During the initial development, the storage is mostly mocked, but
    that will go away as implementation progresses.

    In implementation, don't refer to DefaultOMMStore directly, but
    instead to the interfaces to allow future authors more ease in
    extending.

    Data is stored in a combination of:
      * Static config set by deployment (e.g. installed SignalTypes)
      * PostGres-backed tables (e.g. info downloaded from external APIs)
      * Blobstore (e.g. built indices)
    """

    def get_content_type_configs(self) -> t.Mapping[str, interface.ContentTypeConfig]:
        # TODO
        return MockedUnifiedStore().get_content_type_configs()

    def get_exchange_type_configs(self) -> t.Mapping[str, TSignalExchangeAPICls]:
        # TODO
        return MockedUnifiedStore().get_exchange_type_configs()

    def get_signal_type_configs(self) -> t.Mapping[str, SignalTypeConfig]:
        # TODO
        return MockedUnifiedStore().get_signal_type_configs()

    # Index
    def get_signal_type_index(
        self, signal_type: type[SignalType]
    ) -> t.Optional[SignalTypeIndex[int]]:
        # TODO
        return MockedUnifiedStore().get_signal_type_index(signal_type)

    # Collabs
    def get_collaborations(self) -> t.Dict[str, CollaborationConfigBase]:
        # TODO
        return MockedUnifiedStore().get_collaborations()

    def get_collab_fetch_checkpoint(
        self, collab: CollaborationConfigBase
    ) -> t.Optional[FetchCheckpointBase]:
        return MockedUnifiedStore().get_collab_fetch_checkpoint(collab)

    def commit_collab_fetch_data(
        self,
        collab: CollaborationConfigBase,
        dat: t.Dict[str, t.Any],
        checkpoint: FetchCheckpointBase,
    ) -> None:
        MockedUnifiedStore().commit_collab_fetch_data(collab, dat, checkpoint)

    def get_collab_data(
        self,
        collab_name: str,
        key: str,
        checkpoint: FetchCheckpointBase,
    ) -> t.Any:
        return MockedUnifiedStore().get_collab_data(collab_name, key, checkpoint)
