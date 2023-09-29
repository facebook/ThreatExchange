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

from sqlalchemy import select, update
from OpenMediaMatch import database

from OpenMediaMatch.storage import interface
from OpenMediaMatch.storage.mocked import MockedUnifiedStore
from OpenMediaMatch.storage.interface import (
    SignalTypeConfig,
    BankConfig,
    BankContentConfig,
)


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

    def get_banks(self) -> t.Mapping[str, BankConfig]:
        return {
            b.name: b.as_storage_iface_cls()
            for b in database.db.session.execute(select(database.Bank)).scalars().all()
        }

    def get_bank(self, name: str) -> t.Optional[BankConfig]:
        """Override for more efficient lookup"""
        bank = database.db.session.execute(
            select(database.Bank).where(database.Bank.name == name)
        ).scalar_one_or_none()

        return None if bank is None else bank.as_storage_iface_cls()

    def bank_update(self, bank: BankConfig, *, create: bool = False) -> None:
        if create:
            database.db.session.add(database.Bank.from_storage_iface_cls(bank))
        else:
            database.db.session.execute(
                update(database.Bank)
                .where(database.Bank.name == bank.name)
                .values(enabled_ratio=bank.matching_enabled_ratio)
            )

        database.db.session.commit()

    def bank_delete(self, name: str) -> None:
        # TODO
        raise Exception("Not implemented")

    def bank_content_get(self, id: int) -> BankContentConfig:
        # TODO
        raise Exception("Not implemented")

    def bank_content_update(self, val: BankContentConfig) -> None:
        # TODO
        raise Exception("Not implemented")

    def bank_add_content(
        self,
        bank_name: str,
        content_signals: t.Dict[t.Type[SignalType], str],
        config: t.Optional[BankContentConfig] = None,
    ) -> int:
        # TODO
        raise Exception("Not implemented")

    def bank_remove_content(self, bank_name: str, content_id: int) -> None:
        # TODO
        raise Exception("Not implemented")

    def bank_yield_content(
        self, signal_type: t.Optional[t.Type[SignalType]] = None
    ) -> t.Iterator[t.Sequence[t.Tuple[t.Optional[str], int]]]:
        # TODO
        raise Exception("Not implemented")
