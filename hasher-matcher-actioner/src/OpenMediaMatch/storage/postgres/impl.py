# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
The default store for accessing persistent data on OMM.
"""
from dataclasses import dataclass
import pickle
import time
import typing as t

import flask
import flask_migrate

from sqlalchemy import select, delete, func, Select, insert, update
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import ClauseElement, Executable
from sqlalchemy.ext.compiler import compiles

from threatexchange.exchanges.impl.static_sample import StaticSampleSignalExchangeAPI
from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.content_type.photo import PhotoContent
from threatexchange.content_type.video import VideoContent
from threatexchange.exchanges import auth
from threatexchange.exchanges.signal_exchange_api import (
    TSignalExchangeAPICls,
    TSignalExchangeAPI,
)
from threatexchange.signal_type.index import SignalTypeIndex
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.content_type.content_base import ContentType
from threatexchange.exchanges.fetch_state import (
    FetchCheckpointBase,
    CollaborationConfigBase,
    FetchedSignalMetadata,
    TUpdateRecordKey,
)

from OpenMediaMatch.storage import interface
from threatexchange.cli.storage.interfaces import SignalTypeConfig
from OpenMediaMatch.storage.postgres import database, flask_utils


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

    signal_types: t.Mapping[str, t.Type[SignalType]]
    content_types: t.Mapping[str, t.Type[ContentType]]
    exchange_types: t.Mapping[str, TSignalExchangeAPICls]

    def __init__(
        self,
        *,
        signal_types: t.Sequence[t.Type[SignalType]] | None = None,
        content_types: t.Sequence[t.Type[ContentType]] | None = None,
        exchange_types: t.Sequence[TSignalExchangeAPICls] | None = None,
    ) -> None:
        if signal_types is None:
            signal_types = [PdqSignal, VideoMD5Signal]
        if content_types is None:
            content_types = [PhotoContent, VideoContent]
        if exchange_types is None:
            exchange_types = [StaticSampleSignalExchangeAPI]

        self.signal_types = {st.get_name(): st for st in signal_types}
        self.content_types = {ct.get_name(): ct for ct in content_types}
        self.exchange_types = {et.get_name(): et for et in exchange_types}
        assert len(self.signal_types) == len(
            signal_types
        ), "All signal types must have unique names"
        assert len(self.content_types) == len(
            content_types
        ), "All content types must have unique names"
        assert len(self.exchange_types) == len(
            exchange_types
        ), "All exchange types must have unique names"

    def get_content_type_configs(self) -> t.Mapping[str, interface.ContentTypeConfig]:
        return {
            name: interface.ContentTypeConfig(True, ct)
            for name, ct in self.content_types.items()
        }

    def exchange_apis_get_configs(
        self,
    ) -> t.Mapping[str, interface.SignalExchangeAPIConfig]:
        explicit_settings = {
            s.api: s
            for s in database.db.session.execute(
                select(database.ExchangeAPIConfig)
            ).scalars()
        }

        ret = {}
        for name, api_cls in self.exchange_types.items():
            if name in explicit_settings:
                ret[name] = explicit_settings[name].as_storage_iface_cls(api_cls)
            else:
                ret[name] = interface.SignalExchangeAPIConfig(api_cls)
        return ret

    def exchange_api_config_update(
        self, cfg: interface.SignalExchangeAPIConfig
    ) -> None:
        api_cls = cfg.api_cls
        if cfg.credentials is not None:
            if not issubclass(api_cls, auth.SignalExchangeWithAuth):
                raise ValueError(
                    f"Tried to set credentials for {api_cls.get_name()},"
                    " but it doesn't take them"
                )
            if not isinstance(cfg.credentials, api_cls.get_credential_cls()):
                raise ValueError(
                    "Use the wrong credential class"
                    f" {cfg.credentials.__class__.__name__} for"
                    f" {api_cls.get_name()}"
                )
        sesh = database.db.session
        config = sesh.execute(
            select(database.ExchangeAPIConfig).where(
                database.ExchangeAPIConfig.api == api_cls.get_name()
            )
        ).scalar_one_or_none()
        if config is None:
            config = database.ExchangeAPIConfig(api=api_cls.get_name())
        config.serialize_credentials(cfg.credentials)
        sesh.add(config)
        sesh.commit()

    def get_signal_type_configs(self) -> t.Mapping[str, SignalTypeConfig]:
        # If a signal is installed, then it is enabled by default. But it may be disabled by an
        # override in the database.
        signal_type_overrides = self._query_signal_type_overrides()
        return {
            name: SignalTypeConfig(
                signal_type_overrides.get(name, 1.0),
                st,
            )
            for name, st in self.signal_types.items()
        }

    def _create_or_update_signal_type_override(
        self, signal_type: str, enabled_ratio: float
    ) -> None:
        """Create or update database entry for a signal type, setting a new value."""
        db_record = database.db.session.execute(
            select(database.SignalTypeOverride).where(
                database.SignalTypeOverride.name == signal_type
            )
        ).scalar_one_or_none()
        if db_record is not None:
            db_record.enabled_ratio = enabled_ratio
        else:
            database.db.session.add(
                database.SignalTypeOverride(
                    name=signal_type, enabled_ratio=enabled_ratio
                )
            )

        database.db.session.commit()

    @staticmethod
    def _query_signal_type_overrides() -> dict[str, float]:
        db_records = database.db.session.execute(
            select(database.SignalTypeOverride)
        ).all()
        return {record.name: record.enabled_ratio for record, in db_records}

    # Index
    def get_signal_type_index(
        self, signal_type: type[SignalType]
    ) -> t.Optional[SignalTypeIndex[int]]:
        db_record = database.db.session.execute(
            select(database.SignalIndex).where(
                database.SignalIndex.signal_type == signal_type.get_name()
            )
        ).scalar_one_or_none()

        if db_record is None or not db_record.index_lobj_exists():
            return None
        return db_record.load_signal_index()

    def store_signal_type_index(
        self,
        signal_type: t.Type[SignalType],
        index: SignalTypeIndex,
        checkpoint: interface.SignalTypeIndexBuildCheckpoint,
    ) -> None:
        db_record = database.db.session.execute(
            select(database.SignalIndex).where(
                database.SignalIndex.signal_type == signal_type.get_name()
            )
        ).scalar_one_or_none()
        if db_record is None:
            db_record = database.SignalIndex(
                signal_type=signal_type.get_name(),
            )
            database.db.session.add(db_record)
        db_record.commit_signal_index(index, checkpoint)
        database.db.session.commit()

    def get_last_index_build_checkpoint(
        self, signal_type: t.Type[SignalType]
    ) -> t.Optional[interface.SignalTypeIndexBuildCheckpoint]:
        db_record = database.db.session.execute(
            select(database.SignalIndex).where(
                database.SignalIndex.signal_type == signal_type.get_name()
            )
        ).scalar_one_or_none()

        if db_record is None or not db_record.index_lobj_exists():
            return None
        return db_record.as_checkpoint()

    # Collabs
    def exchange_update(
        self, cfg: CollaborationConfigBase, *, create: bool = False
    ) -> None:
        if create:
            bank = database.Bank(name=cfg.name)
            exchange = database.ExchangeConfig(import_bank=bank)
        else:
            exchange = database.db.session.execute(
                select(database.ExchangeConfig).where(
                    database.ExchangeConfig.name == cfg.name
                )
            ).scalar_one()
        exchange.set_typed_config(cfg)
        database.db.session.add(exchange)
        database.db.session.commit()

    def exchange_delete(self, name: str) -> None:
        database.db.session.execute(
            delete(database.ExchangeConfig).where(database.ExchangeConfig.name == name)
        )
        database.db.session.commit()

    def exchanges_get(self) -> t.Dict[str, CollaborationConfigBase]:
        results = database.db.session.execute(select(database.ExchangeConfig)).scalars()
        return {
            cfg.name: cfg.as_storage_iface_cls(self.exchange_types) for cfg in results
        }

    def _exchange_get_cfg(self, name: str) -> t.Optional[database.ExchangeConfig]:
        return database.db.session.execute(
            select(database.ExchangeConfig).where(database.ExchangeConfig.name == name)
        ).scalar_one_or_none()

    def exchange_get_client(
        self, collab_config: CollaborationConfigBase
    ) -> TSignalExchangeAPI:
        cfg = self.exchange_apis_get_configs().get(collab_config.api)
        assert cfg is not None, f"No such exchange API {collab_config.api}"

        creds = cfg.credentials
        if creds is None:
            return cfg.api_cls.for_collab(collab_config)

        # Why did I make this interface so dumb?
        with creds.set_default(creds, "db"):
            return cfg.api_cls.for_collab(collab_config)

    def exchange_get_fetch_status(self, name: str) -> interface.FetchStatus:
        collab_config = self._exchange_get_cfg(name)
        assert collab_config is not None, "Config was deleted?"
        status = collab_config.fetch_status
        if status is None:
            return interface.FetchStatus.get_default()
        ret = status.as_storage_iface_cls()

        query = database.db.session.query(database.ExchangeData).where(
            database.ExchangeData.collab_id == collab_config.id
        )
        statement = t.cast(Select[database.ExchangeData], query.statement)
        count = query.session.execute(
            statement.with_only_columns(func.count()).order_by(None)
        ).scalar()
        ret.fetched_items = count or 0
        return ret

    def exchange_get_fetch_checkpoint(
        self, name: str
    ) -> t.Optional[FetchCheckpointBase]:
        collab_config = self._exchange_get_cfg(name)
        assert collab_config is not None, "Config was deleted?"
        return collab_config.as_checkpoint(self.exchange_apis_get_installed())

    def exchange_start_fetch(self, collab_name: str) -> None:
        cfg = self._exchange_get_cfg(collab_name)
        assert cfg is not None, "Config was deleted?"
        fetch_status = cfg.fetch_status
        if fetch_status is None:
            fetch_status = database.ExchangeFetchStatus()
            fetch_status.collab = cfg
            database.db.session.add(fetch_status)
        fetch_status.running_fetch_start_ts = int(time.time())
        database.db.session.commit()

    def exchange_complete_fetch(
        self, collab_name: str, *, is_up_to_date: bool, exception: bool
    ) -> None:
        if exception is True:
            database.db.session.rollback()
        cfg = self._exchange_get_cfg(collab_name)
        assert cfg is not None, "Config was deleted?"
        fetch_status = cfg.fetch_status
        if fetch_status is None:
            fetch_status = database.ExchangeFetchStatus()
            fetch_status.collab = cfg
            database.db.session.add(fetch_status)
        fetch_status.running_fetch_start_ts = None
        fetch_status.last_fetch_complete_ts = int(time.time())
        fetch_status.last_fetch_succeeded = not exception
        fetch_status.is_up_to_date = is_up_to_date
        database.db.session.commit()

    def exchange_commit_fetch(
        self,
        collab: CollaborationConfigBase,
        old_checkpoint: t.Optional[FetchCheckpointBase],
        dat: t.Dict[t.Any, t.Any],
        checkpoint: FetchCheckpointBase,
    ) -> None:
        cfg = self._exchange_get_cfg(collab.name)
        assert cfg is not None, "Config was deleted?"
        fetch_status = cfg.fetch_status
        existing_checkpoint = cfg.as_checkpoint(self.exchange_apis_get_installed())
        assert (
            existing_checkpoint == old_checkpoint
        ), "Old checkpoint doesn't match, race condition?"

        api_cls = self.exchange_apis_get_installed().get(collab.api)
        assert api_cls is not None, "Invalid API cls?"
        collab_config = cfg.as_storage_iface_cls_typed(api_cls)

        sesh = database.db.session

        # To optimize what is essentially a bulk insert,
        # we break this up into four passes:
        # 1. Select all the existing records with the given keys, already joined
        # 2. Partition the existing ExportData records into creates, updates, and deletes - execute those
        # 3. Create any missing bankable content
        # 4. Partition the signal updates into creates and deletes - execute those
        # Commit

        # Pass 1 - select the full state already in the database
        existing_xds = {
            record.fetch_id: record
            for record in sesh.execute(
                select(database.ExchangeData)
                .where(database.ExchangeData.collab_id == cfg.id)
                .where(database.ExchangeData.fetch_id.in_([str(k) for k in dat]))
                .options(
                    joinedload(database.ExchangeData.bank_content).joinedload(
                        database.BankContent.signals
                    )
                )
            )
            .unique()
            .scalars()
        }

        xd_to_create: list[t.Tuple[dict[str, t.Any], _BulkDbOpExchangeDataHelper]] = []
        xd_to_update = []
        xd_to_delete = []
        op_helpers = {}

        signal_types = list(self.signal_types.values())

        # Pass 1 - Collect bulk create/update/dete the ExchageData
        for raw_k, val in dat.items():
            k = str(raw_k)
            xd = existing_xds.get(k)
            as_signal_types = {}
            if val is not None:
                as_signal_types = api_cls.naive_convert_to_signal_type(
                    signal_types, collab_config, {raw_k: val}
                )
                # If we can't use any of the data in the record, treat it as a
                # delete to save space, unless we are specifically configured to
                # retain it
                if not as_signal_types:
                    val = None
            if val is None:
                if xd is not None:
                    xd_to_delete.append(xd.id)
                continue

            pickled_fetch_signal_metadata = pickle.dumps(val)

            if xd is None:
                xd_to_create.append(
                    (
                        {
                            "collab_id": cfg.id,
                            "fetch_id": k,
                            "pickled_fetch_signal_metadata": pickled_fetch_signal_metadata,
                        },
                        _BulkDbOpExchangeDataHelper.from_creation(as_signal_types),
                    )
                )
            else:
                op_helpers[xd.id] = (
                    _BulkDbOpExchangeDataHelper.from_existing_exchange_data(
                        xd, as_signal_types
                    )
                )
                if pickled_fetch_signal_metadata != xd.pickled_fetch_signal_metadata:
                    xd_to_update.append(
                        {
                            "id": xd.id,
                            "pickled_fetch_signal_metadata": pickled_fetch_signal_metadata,
                        }
                    )

        if xd_to_create:
            created_ids = sesh.scalars(
                insert(database.ExchangeData).returning(
                    database.ExchangeData.id, sort_by_parameter_order=True
                ),
                [t[0] for t in xd_to_create],
            ).all()

            assert len(created_ids) == len(xd_to_create)
            for id, (_, op_helper) in zip(created_ids, xd_to_create):
                op_helper.exchange_data_id = id
                op_helpers[id] = op_helper

        if xd_to_update:
            sesh.execute(update(database.ExchangeData), xd_to_update)
        if xd_to_delete:
            sesh.execute(
                delete(database.ExchangeData).where(
                    database.ExchangeData.id.in_(xd_to_delete)
                )
            )
        sesh.flush()
        _sync_bankable_content(op_helpers, cfg.import_bank.id)
        _sync_content_signal(op_helpers)

        if fetch_status is None:
            fetch_status = database.ExchangeFetchStatus(collab=cfg)
        fetch_status.set_checkpoint(checkpoint)

        sesh.add(fetch_status)
        sesh.commit()

    def exchange_get_data(
        self,
        collab_name: str,
        key: TUpdateRecordKey,
    ) -> FetchedSignalMetadata:
        cfg = self._exchange_get_cfg(collab_name)
        if cfg is None:
            raise KeyError(f"No such config '{collab_name}'")

        res = database.db.session.execute(
            select(database.ExchangeData)
            .where(database.ExchangeData.collab_id == cfg.id)
            .where(database.ExchangeData.fetch_id == str(key))
        ).scalar_one_or_none()
        if res is None:
            raise KeyError("No exchange data with name and key")
        dat = res.pickled_fetch_signal_metadata
        assert dat is not None
        return pickle.loads(dat)

    def get_banks(self) -> t.Mapping[str, interface.BankConfig]:
        return {
            b.name: b.as_storage_iface_cls()
            for b in database.db.session.execute(select(database.Bank)).scalars().all()
        }

    def get_bank(self, name: str) -> t.Optional[interface.BankConfig]:
        """Override for more efficient lookup."""
        bank = database.db.session.execute(
            select(database.Bank).where(database.Bank.name == name)
        ).scalar_one_or_none()

        return None if bank is None else bank.as_storage_iface_cls()

    def _get_bank(self, name: str) -> t.Optional[database.Bank]:
        return database.db.session.execute(
            select(database.Bank).where(database.Bank.name == name)
        ).scalar_one_or_none()

    def bank_update(
        self,
        bank: interface.BankConfig,
        *,
        create: bool = False,
        rename_from: t.Optional[str] = None,
    ) -> None:
        if create:
            database.db.session.add(database.Bank.from_storage_iface_cls(bank))
        else:
            previous = database.Bank.query.filter_by(
                name=rename_from if rename_from is not None else bank.name
            ).one_or_404()
            previous.name = bank.name
            previous.enabled_ratio = bank.matching_enabled_ratio

        database.db.session.commit()

    def bank_delete(self, name: str) -> None:
        database.db.session.execute(
            delete(database.Bank).where(database.Bank.name == name)
        )
        database.db.session.commit()

    def bank_content_get(
        self, ids: t.Iterable[int]
    ) -> t.Sequence[interface.BankContentConfig]:
        return [
            b.as_storage_iface_cls()
            for b in database.db.session.query(database.BankContent)
            .filter(database.BankContent.id.in_(ids))
            .all()
        ]

    def bank_content_update(self, val: interface.BankContentConfig) -> None:
        # TODO
        raise Exception("Not implemented")

    def bank_add_content(
        self,
        bank_name: str,
        content_signals: t.Dict[t.Type[SignalType], str],
        config: t.Optional[interface.BankContentConfig] = None,
    ) -> int:
        # Add content to the bank provided.
        # Returns the ID of the content added.
        sesh = database.db.session

        bank = self._get_bank(bank_name)
        content = database.BankContent(bank=bank)
        if config is not None:
            content.original_content_uri = config.original_media_uri
        sesh.add(content)
        for content_signal, value in content_signals.items():
            hash = database.ContentSignal(
                content=content,
                signal_type=content_signal.get_name(),
                signal_val=value,
            )
            sesh.add(hash)

        sesh.commit()
        return content.id

    def bank_remove_content(self, bank_name: str, content_id: int) -> int:
        # TODO: throw an exception if deleting imported content
        result = database.db.session.execute(
            delete(database.BankContent).where(database.BankContent.id == content_id)
        )
        database.db.session.commit()
        return result.rowcount

    def get_current_index_build_target(
        self, signal_type: t.Type[SignalType]
    ) -> interface.SignalTypeIndexBuildCheckpoint:
        query = database.db.session.query(database.ContentSignal).where(
            database.ContentSignal.signal_type == signal_type.get_name()
        )
        statement = t.cast(Select[database.ContentSignal], query.statement)
        count = query.session.execute(
            statement.with_only_columns(func.count()).order_by(None)
        ).scalar()

        if not count:
            return interface.SignalTypeIndexBuildCheckpoint.get_empty()

        # Count non-zero, so get where we are in the order
        row = database.db.session.execute(
            select(
                database.ContentSignal.create_time, database.ContentSignal.content_id
            )
            .where(database.ContentSignal.signal_type == signal_type.get_name())
            .order_by(
                database.ContentSignal.create_time.desc(),
                database.ContentSignal.content_id.desc(),
            )
            .limit(1)
        ).one()
        create_datetime, content_id = row._tuple()

        return interface.SignalTypeIndexBuildCheckpoint(
            last_item_id=content_id,
            last_item_timestamp=int(create_datetime.timestamp()),
            total_hash_count=count,
        )

    def bank_yield_content(
        self, signal_type: t.Optional[t.Type[SignalType]] = None, batch_size: int = 100
    ) -> t.Iterator[interface.BankContentIterationItem]:
        # Query for all ContentSignals and stream results with the proper batch size
        query = (
            select(database.ContentSignal)
            .order_by(
                database.ContentSignal.signal_type,
                database.ContentSignal.create_time,
                database.ContentSignal.content_id,
            )
            .execution_options(stream_results=True, max_row_buffer=batch_size)
        )

        # Conditionally apply the filter if signal_type is provided
        if signal_type is not None:
            query = query.filter(
                database.ContentSignal.signal_type == signal_type.get_name()
            )

        # Execute the query and stream results with the proper yield batch size
        result = database.db.session.execute(query).yield_per(batch_size)

        for partition in result.partitions():
            # If there are no more results, break the loop
            if not partition:
                break

            # Yield the results as tuples (signal_val, content_id)
            for row in partition:
                yield row._tuple()[0].as_iteration_item()

    def init_flask(self, app: flask.Flask) -> None:
        migrate = flask_migrate.Migrate()
        database.db.init_app(app)
        migrate.init_app(app, database.db)
        flask_utils.add_cli_commands(app)


def _sync_bankable_content(
    # ops is modified during the course of the function
    ops: dict[int, "_BulkDbOpExchangeDataHelper"],
    bank_id: int,
) -> None:
    """
    Middle pass: sync the expected state of bankable content
    """
    sesh = database.db.session
    bc_id_to_delete = []
    for xd_id in list(ops):
        op = ops[xd_id]
        if op.update_as_signals:
            continue
        # We don't need the ops that have no signals - we'll delete them
        # at this step.
        del ops[xd_id]
        if op.bank_content_id is not None:
            bc_id_to_delete.append(op.bank_content_id)
    if bc_id_to_delete:
        sesh.execute(delete(database.BankContent), {"id": id for id in bc_id_to_delete})
    to_create = [op for op in ops.values() if op.bank_content_id is None]
    if not to_create:
        return
    created_ids = sesh.scalars(
        insert(database.BankContent).returning(
            database.BankContent.id, sort_by_parameter_order=True
        ),
        [
            {"bank_id": bank_id, "imported_from_id": op.exchange_data_id}
            for op in to_create
        ],
    )
    for id, op in zip(created_ids, to_create):
        op.bank_content_id = id
    sesh.flush()


def _sync_content_signal(
    ops: dict[int, "_BulkDbOpExchangeDataHelper"],
) -> None:
    """
    Final pass: insert/delete content_signal
    """
    sesh = database.db.session
    to_add: list[dict[str, t.Any]] = []
    to_delete: list[database.ContentSignal] = []
    for op in ops.values():
        unseen_signals_in_db_for_fetch_key = {
            (signal.signal_type, signal.signal_val): signal
            for signal in op.existing_signals
        }

        # Additions / modifications
        for signal_type, signal_to_metadata in op.update_as_signals.items():
            for signal_value in signal_to_metadata:
                # TODO - check the metadata for signals for opinions we own
                #        that have false-positive on them.
                k = (signal_type.get_name(), signal_value)
                if k in unseen_signals_in_db_for_fetch_key:
                    # If we need to sync the record, here's where we do it
                    # Remove from the list of signals
                    del unseen_signals_in_db_for_fetch_key[k]
                else:
                    to_add.append(
                        {
                            "content_id": op.bank_content_id,
                            "signal_type": signal_type.get_name(),
                            "signal_val": signal_value,
                        }
                    )
        # Removals
        # At this point, we've popped all the ones that are still in the record
        # Any left are ones that have been removed from the API copy
        for cs in unseen_signals_in_db_for_fetch_key.values():
            to_delete.append(cs)

    # Noo! No bulk delete at the moment, sequential it is
    for cs in to_delete:
        sesh.delete(cs)
    if to_add:
        sesh.execute(insert(database.ContentSignal), to_add)


@dataclass
class _BulkDbOpExchangeDataHelper:
    """
    Tracking data for the complex exchange_commit_fetch function
    """

    exchange_data_id: int | None
    bank_content_id: int | None
    existing_signals: list[database.ContentSignal]
    update_as_signals: dict[type[SignalType], dict[str, FetchedSignalMetadata]]

    @classmethod
    def from_existing_exchange_data(
        cls,
        exchange_data: database.ExchangeData,
        update_as_signals: dict[type[SignalType], dict[str, FetchedSignalMetadata]],
    ) -> t.Self:
        bc = exchange_data.bank_content
        existing_signals = []
        if bc is not None:
            existing_signals = bc.signals
        return cls(
            exchange_data.id,
            None if bc is None else bc.id,
            existing_signals,
            update_as_signals,
        )

    @classmethod
    def from_creation(
        cls, update_as_signals: dict[type[SignalType], dict[str, FetchedSignalMetadata]]
    ) -> t.Self:
        return cls(None, None, [], update_as_signals)


def explain(q, analyze: bool = False):
    """
    Debugging tool to help test query optimization.

    How to use:

    q = select(database.Blah).where(...).order_by(...)...
    print(explain(q))

    """
    return database.db.session.execute(_explain(q, analyze)).fetchall()


class _explain(Executable, ClauseElement):
    """
    Debugging tool to help test query optimization.

    How to use:

    q = select(database.Blah).where(...).order_by(...)...
    print(database.db.session.execute(_explain(q)).fetchall())
    """

    def __init__(self, stmt, analyze: bool = False):
        self.statement = stmt
        self.analyze = analyze


@compiles(_explain, "postgresql")
def _pg_explain(element: _explain, compiler, **kw):
    text = "EXPLAIN "
    if element.analyze:
        text += "ANALYZE "
    text += compiler.process(element.statement, **kw)

    return text
