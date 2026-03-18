# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Simple dbm implementation of the storage interface.
"""

import dbm
from enum import Enum
from dataclasses import dataclass
import json
import time
import typing as t
from pathlib import Path

from threatexchange.utils import dataclass_json
from threatexchange.storage import interfaces as iface
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.content_type.content_base import ContentType
from threatexchange.exchanges import auth
from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.exchanges.fetch_state import FetchCheckpointBase, TUpdateRecordKey
from threatexchange.exchanges.signal_exchange_api import (
    TSignalExchangeAPI,
    TSignalExchangeAPICls,
)
from threatexchange.exchanges.impl.static_sample import StaticSampleSignalExchangeAPI
from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.content_type.photo import PhotoContent
from threatexchange.content_type.video import VideoContent


class _DbType(Enum):
    SIGNAL_TYPE = "signal_type"
    CONTENT_TYPE = "content_type"
    EXCHANGE_TYPE = "exchange_type"
    EXCHANGES = "exchanges"
    EXCHANGE_STATUS = "exchange_status"
    EXCHANGE_DATA = "exchange_data"
    BANKS = "banks"
    INDEX = "index"
    BANK_CONTENT = "bank_content"


@dataclass
class _SignalTypeCfg:
    enabled_ratio: float = 1.0


@dataclass
class _ContentTypeCfg:
    enabled: bool = True


@dataclass
class _ExchangeCollab:
    """Stored collab config: api name + JSON-serialized collab config dataclass."""

    api: str
    config_json: str  # dataclass_dumps of CollaborationConfigBase subclass


@dataclass
class _ExchangeStatus:
    """Per-collab fetch state: timestamps + JSON-serialized checkpoint."""

    checkpoint_json: t.Optional[str] = (
        None  # dataclass_dumps of FetchCheckpointBase subclass
    )
    checkpoint_ts: t.Optional[int] = None
    running_fetch_start_ts: t.Optional[int] = None
    last_fetch_complete_ts: t.Optional[int] = None
    last_fetch_succeeded: t.Optional[bool] = None
    up_to_date: bool = False


@dataclass
class _ExchangeAPICredsCfg:
    """Stored API-level credentials: JSON-serialized CredentialHelper subclass."""

    credentials_json: t.Optional[str] = (
        None  # dataclass_dumps of CredentialHelper subclass
    )


@dataclass
class _BankStoredContent:
    """
    Stored representation of a bank content item, including all its signals.

    Signals are embedded here rather than stored as separate keys, since
    there is no fast lookup needed by signal value — indices store content_id.
    """

    id: int
    disable_until_ts: int
    collab_metadata: t.Dict[str, t.List[str]]  # concrete types for JSON roundtrip
    original_media_uri: t.Optional[str]
    created_ts: int  # set at insert, preserved on update; used for index checkpoint
    signals: t.Dict[str, str]  # signal_type_name -> signal_value


def _key_str(key: t.Any) -> str:
    """Convert a TUpdateRecordKey to a stable string for DBM storage."""
    if isinstance(key, tuple):
        return json.dumps(list(key))
    return json.dumps(key)


_NEXT_ID_KEY = b"__next_id__"


def _content_key(content_id: int) -> bytes:
    """Key for a bank content record in the per-bank DBM."""
    return str(content_id).encode()


# TODO - eventually to unified store
class DBMStore(
    iface.ISignalTypeConfigStore,
    iface.IContentTypeConfigStore,
    iface.ISignalExchangeStore,
    iface.IBankStore,
):
    """
    Local machine storage based on python dbm library,

    A simple one-machine storage interface, which persists on disk.
    Useful for testing or single machine work.
    """

    _folder: Path
    signal_types: t.Mapping[str, t.Type[SignalType]]
    content_types: t.Mapping[str, t.Type[ContentType]]
    exchange_types: t.Mapping[str, TSignalExchangeAPICls]

    def __init__(
        self,
        folder: Path,
        *,
        signal_types: t.Optional[t.Sequence[t.Type[SignalType]]] = None,
        content_types: t.Optional[t.Sequence[t.Type[ContentType]]] = None,
        exchange_types: t.Optional[t.Sequence[TSignalExchangeAPICls]] = None,
    ) -> None:
        assert folder.is_dir(), "must be path"
        self._folder = folder

        if signal_types is None:
            signal_types = [PdqSignal, VideoMD5Signal]
        if content_types is None:
            content_types = [PhotoContent, VideoContent]
        if exchange_types is None:
            exchange_types = t.cast(
                t.Sequence[TSignalExchangeAPICls], [StaticSampleSignalExchangeAPI]
            )

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

    def _open(self, db: _DbType, *, sub_db: str = ""):
        file = self._folder / str(db)
        if sub_db:
            file = file / sub_db
        return dbm.open(str(file), "c")

    def _open_collab_data(self, collab_name: str):
        """Open a per-collab exchange data db in its own subfolder."""
        d = self._folder / str(_DbType.EXCHANGE_DATA)
        d.mkdir(exist_ok=True)
        return dbm.open(str(d / collab_name), "c")

    def _open_bank_content(self, bank_name: str):
        """Open the per-bank content DBM file, creating the directory if needed."""
        d = self._folder / str(_DbType.BANK_CONTENT)
        d.mkdir(exist_ok=True)
        return dbm.open(str(d / bank_name), "c")

    def _get_next_id(self) -> int:
        """
        Allocate and return the next globally unique content ID.

        Stores the counter under the reserved key __next_id__ in the BANKS
        metadata DB. Safe for single-process use (no concurrent writers).
        IDs start at 1; 0 is reserved as a sentinel.
        """
        with self._open(_DbType.BANKS) as db:
            raw = db.get(_NEXT_ID_KEY)
            next_id = int(raw.decode()) if raw is not None else 1
            db[_NEXT_ID_KEY] = str(next_id + 1).encode()
        return next_id

    def get_signal_type_configs(self) -> t.Mapping[str, iface.SignalTypeConfig]:
        """Return all installed signal types."""
        with self._open(_DbType.SIGNAL_TYPE) as db:
            ret = {}
            for name, st in self.signal_types.items():
                raw_cfg = db.get(name)
                cfg = _SignalTypeCfg()
                if raw_cfg is not None:
                    cfg = dataclass_json.dataclass_loads(
                        raw_cfg.decode(), _SignalTypeCfg
                    )
                ret[name] = iface.SignalTypeConfig(
                    signal_type=st,
                    enabled_ratio=cfg.enabled_ratio,
                )
        return ret

    def _create_or_update_signal_type_override(
        self, signal_type: str, enabled_ratio: float
    ) -> None:
        with self._open(_DbType.SIGNAL_TYPE) as db:
            db[signal_type] = dataclass_json.dataclass_dumps(
                _SignalTypeCfg(enabled_ratio=enabled_ratio)
            ).encode()

    def get_content_type_configs(self) -> t.Mapping[str, iface.ContentTypeConfig]:
        """Return all installed content types, merged with any stored overrides."""
        with self._open(_DbType.CONTENT_TYPE) as db:
            ret = {}
            for name, ct in self.content_types.items():
                raw_cfg = db.get(name)
                cfg = _ContentTypeCfg()
                if raw_cfg is not None:
                    cfg = dataclass_json.dataclass_loads(
                        raw_cfg.decode(), _ContentTypeCfg
                    )
                ret[name] = iface.ContentTypeConfig(
                    content_type=ct,
                    enabled=cfg.enabled,
                )
        return ret

    def _create_or_update_content_type_override(
        self, content_type: str, enabled: bool
    ) -> None:
        with self._open(_DbType.CONTENT_TYPE) as db:
            db[content_type] = dataclass_json.dataclass_dumps(
                _ContentTypeCfg(enabled=enabled)
            ).encode()

    # ISignalExchangeStore

    def exchange_apis_get_configs(
        self,
    ) -> t.Mapping[str, iface.SignalExchangeAPIConfig]:
        """Returns the configuration for all installed exchange types."""
        ret = {}
        with self._open(_DbType.EXCHANGE_TYPE) as db:
            for name, api_cls in self.exchange_types.items():
                raw = db.get(name)
                credentials = None
                if raw is not None:
                    cfg = dataclass_json.dataclass_loads(
                        raw.decode(), _ExchangeAPICredsCfg
                    )
                    if cfg.credentials_json is not None and issubclass(
                        api_cls, auth.SignalExchangeWithAuth
                    ):
                        cred_cls = t.cast(
                            t.Type[auth.SignalExchangeWithAuth], api_cls
                        ).get_credential_cls()
                        credentials = dataclass_json.dataclass_loads(
                            cfg.credentials_json, cred_cls
                        )
                ret[name] = iface.SignalExchangeAPIConfig(
                    api_cls=api_cls, credentials=credentials
                )
        return ret

    def exchange_api_config_update(self, cfg: iface.SignalExchangeAPIConfig) -> None:
        """Update the config for an installed exchange API."""
        credentials_json = None
        if cfg.credentials is not None:
            credentials_json = dataclass_json.dataclass_dumps(cfg.credentials)
        stored = _ExchangeAPICredsCfg(credentials_json=credentials_json)
        with self._open(_DbType.EXCHANGE_TYPE) as db:
            db[cfg.api_cls.get_name()] = dataclass_json.dataclass_dumps(stored).encode()

    def exchange_update(
        self, cfg: CollaborationConfigBase, *, create: bool = False
    ) -> None:
        """Create or update a collaboration."""
        with self._open(_DbType.EXCHANGES) as db:
            exists = db.get(cfg.name) is not None
            if create and exists:
                raise ValueError(f"Collaboration {cfg.name!r} already exists")
            if not create and not exists:
                raise ValueError(f"Collaboration {cfg.name!r} does not exist")
            collab = _ExchangeCollab(
                api=cfg.api,
                config_json=dataclass_json.dataclass_dumps(cfg),
            )
            db[cfg.name] = dataclass_json.dataclass_dumps(collab).encode()

    def exchange_delete(self, name: str) -> None:
        """Delete a collaboration and all its associated data."""
        with self._open(_DbType.EXCHANGES) as db:
            if name in db:
                del db[name]
        with self._open(_DbType.EXCHANGE_STATUS) as db:
            if name in db:
                del db[name]
        # Delete the per-collab data db file(s). Different dbm backends create
        # files with different extensions, so try all known suffixes.
        base = self._folder / str(_DbType.EXCHANGE_DATA) / name
        for ext in ("", ".db", ".dir", ".dat", ".bak"):
            base.with_name(base.name + ext).unlink(missing_ok=True)

    def exchanges_get(self) -> t.Mapping[str, CollaborationConfigBase]:
        """Get all collaboration configs."""
        ret = {}
        with self._open(_DbType.EXCHANGES) as db:
            for raw_name in db.keys():
                name = raw_name.decode() if isinstance(raw_name, bytes) else raw_name
                raw = db[raw_name]
                collab_data = dataclass_json.dataclass_loads(
                    raw.decode(), _ExchangeCollab
                )
                api_cls = self.exchange_types.get(collab_data.api)
                if api_cls is None:
                    continue
                config_cls = api_cls.get_config_cls()
                ret[name] = dataclass_json.dataclass_loads(
                    collab_data.config_json, config_cls
                )
        return ret

    def exchange_get_fetch_status(self, name: str) -> iface.FetchStatus:
        """Get the last fetch status."""
        with self._open(_DbType.EXCHANGE_STATUS) as db:
            raw = db.get(name)
            if raw is None:
                status = _ExchangeStatus()
            else:
                status = dataclass_json.dataclass_loads(raw.decode(), _ExchangeStatus)
        with self._open_collab_data(name) as db:
            fetched_items = len(db)
        return iface.FetchStatus(
            checkpoint_ts=status.checkpoint_ts,
            running_fetch_start_ts=status.running_fetch_start_ts,
            last_fetch_complete_ts=status.last_fetch_complete_ts,
            last_fetch_succeeded=status.last_fetch_succeeded,
            up_to_date=status.up_to_date,
            fetched_items=fetched_items,
        )

    def exchange_get_fetch_checkpoint(
        self, name: str
    ) -> t.Optional[FetchCheckpointBase]:
        """Get the last fetch checkpoint."""
        with self._open(_DbType.EXCHANGE_STATUS) as db:
            raw = db.get(name)
            if raw is None:
                return None
            status = dataclass_json.dataclass_loads(raw.decode(), _ExchangeStatus)
            if status.checkpoint_json is None:
                return None
        with self._open(_DbType.EXCHANGES) as db:
            raw_collab = db.get(name)
            if raw_collab is None:
                return None
            collab_data = dataclass_json.dataclass_loads(
                raw_collab.decode(), _ExchangeCollab
            )
        api_cls = self.exchange_types.get(collab_data.api)
        if api_cls is None:
            return None
        checkpoint_cls = api_cls.get_checkpoint_cls()
        return dataclass_json.dataclass_loads(status.checkpoint_json, checkpoint_cls)

    def exchange_get_client(
        self, collab_config: CollaborationConfigBase
    ) -> TSignalExchangeAPI:
        """Return an authenticated client for a collaboration."""
        cfg = self.exchange_apis_get_configs().get(collab_config.api)
        assert cfg is not None, f"No such exchange API {collab_config.api!r}"
        creds = cfg.credentials
        if creds is None:
            return cfg.api_cls.for_collab(collab_config)
        with creds.set_default(creds, "db"):
            return cfg.api_cls.for_collab(collab_config)

    def exchange_start_fetch(self, collab_name: str) -> None:
        """Record the start of a fetch attempt."""
        with self._open(_DbType.EXCHANGE_STATUS) as db:
            raw = db.get(collab_name)
            status = (
                dataclass_json.dataclass_loads(raw.decode(), _ExchangeStatus)
                if raw is not None
                else _ExchangeStatus()
            )
            status.running_fetch_start_ts = int(time.time())
            db[collab_name] = dataclass_json.dataclass_dumps(status).encode()

    def exchange_complete_fetch(
        self, collab_name: str, *, is_up_to_date: bool, exception: bool
    ) -> None:
        """Record that the fetch has completed."""
        with self._open(_DbType.EXCHANGE_STATUS) as db:
            raw = db.get(collab_name)
            status = (
                dataclass_json.dataclass_loads(raw.decode(), _ExchangeStatus)
                if raw is not None
                else _ExchangeStatus()
            )
            status.running_fetch_start_ts = None
            status.last_fetch_complete_ts = int(time.time())
            status.last_fetch_succeeded = not exception
            status.up_to_date = is_up_to_date
            db[collab_name] = dataclass_json.dataclass_dumps(status).encode()

    def exchange_commit_fetch(
        self,
        collab: CollaborationConfigBase,
        old_checkpoint: t.Optional[FetchCheckpointBase],
        dat: t.Dict[t.Any, t.Any],
        checkpoint: FetchCheckpointBase,
    ) -> None:
        """Commit fetched data and update the checkpoint."""
        with self._open_collab_data(collab.name) as db:
            for key, val in dat.items():
                db_key = _key_str(key).encode()
                if val is None:
                    if db_key in db:
                        del db[db_key]
                else:
                    db[db_key] = dataclass_json.dataclass_dumps(val).encode()
        with self._open(_DbType.EXCHANGE_STATUS) as db:
            raw = db.get(collab.name)
            status = (
                dataclass_json.dataclass_loads(raw.decode(), _ExchangeStatus)
                if raw is not None
                else _ExchangeStatus()
            )
            status.checkpoint_json = dataclass_json.dataclass_dumps(checkpoint)
            ts = checkpoint.get_progress_timestamp()
            status.checkpoint_ts = ts if ts is not None else int(time.time())
            db[collab.name] = dataclass_json.dataclass_dumps(status).encode()

    def exchange_get_data(
        self,
        collab_name: str,
        key: TUpdateRecordKey,
    ) -> iface.FetchedSignalMetadata:
        """Return the stored metadata for a fetched record."""
        with self._open(_DbType.EXCHANGES) as db:
            raw_collab = db.get(collab_name)
            if raw_collab is None:
                raise KeyError(f"No such collaboration: {collab_name!r}")
            collab_data = dataclass_json.dataclass_loads(
                raw_collab.decode(), _ExchangeCollab
            )
        api_cls = self.exchange_types.get(collab_data.api)
        if api_cls is None:
            raise KeyError(f"Unknown exchange API: {collab_data.api!r}")
        record_cls = api_cls.get_record_cls()
        with self._open_collab_data(collab_name) as db:
            raw = db.get(_key_str(key).encode())
            if raw is None:
                raise KeyError(
                    f"No data for key {key!r} in collaboration {collab_name!r}"
                )
            return dataclass_json.dataclass_loads(raw.decode(), record_cls)

    # IBankStore

    def get_banks(self) -> t.Mapping[str, iface.BankConfig]:
        """Return all bank configs."""
        with self._open(_DbType.BANKS) as db:
            ret = {}
            for raw_key in db.keys():
                key = raw_key.decode() if isinstance(raw_key, bytes) else raw_key
                if key.startswith("__"):
                    continue  # skip reserved keys like __next_id__
                raw_val = db[raw_key]
                ret[key] = dataclass_json.dataclass_loads(
                    raw_val.decode(), iface.BankConfig
                )
            return ret

    def bank_update(
        self,
        bank: iface.BankConfig,
        *,
        create: bool = False,
        rename_from: t.Optional[str] = None,
    ) -> None:
        """Update a bank config. Handles creation and rename."""
        with self._open(_DbType.BANKS) as db:
            exists = db.get(bank.name) is not None
            if create and exists:
                raise ValueError(f"Bank {bank.name!r} already exists")
            if not create and not exists and rename_from is None:
                raise ValueError(f"Bank {bank.name!r} does not exist")
            if rename_from is not None:
                old_key = (
                    rename_from.encode()
                    if not isinstance(rename_from, bytes)
                    else rename_from
                )
                if old_key in db:
                    del db[old_key]
            db[bank.name] = dataclass_json.dataclass_dumps(bank).encode()
        if rename_from is not None:
            # Rename the per-bank content DBM file(s) on disk.
            # Different dbm backends create different file extensions.
            d = self._folder / str(_DbType.BANK_CONTENT)
            old_base = d / rename_from
            new_base = d / bank.name
            for ext in ("", ".db", ".dir", ".dat", ".bak"):
                old = old_base.with_name(old_base.name + ext)
                new = new_base.with_name(new_base.name + ext)
                if old.exists():
                    old.rename(new)

    def bank_delete(self, name: str) -> None:
        """Delete a bank and all its content. No exception if bank doesn't exist."""
        with self._open(_DbType.BANKS) as db:
            key = name.encode() if not isinstance(name, bytes) else name
            if key in db:
                del db[key]
        d = self._folder / str(_DbType.BANK_CONTENT)
        base = d / name
        for ext in ("", ".db", ".dir", ".dat", ".bak"):
            base.with_name(base.name + ext).unlink(missing_ok=True)

    def bank_content_get(
        self, id: t.Iterable[int]
    ) -> t.Sequence[iface.BankContentConfig]:
        """Get content configs for a set of IDs, searching across all banks."""
        remaining = set(id)
        if not remaining:
            return []
        results = []
        all_banks = self.get_banks()
        for bank_name, bank_cfg in all_banks.items():
            if not remaining:
                break
            with self._open_bank_content(bank_name) as db:
                for content_id in list(remaining):
                    raw = db.get(_content_key(content_id))
                    if raw is not None:
                        stored = dataclass_json.dataclass_loads(
                            raw.decode(), _BankStoredContent
                        )
                        results.append(
                            iface.BankContentConfig(
                                id=stored.id,
                                disable_until_ts=stored.disable_until_ts,
                                collab_metadata=stored.collab_metadata,
                                original_media_uri=stored.original_media_uri,
                                bank=bank_cfg,
                            )
                        )
                        remaining.discard(content_id)
        return results

    def bank_content_get_signals(
        self, id: t.Iterable[int]
    ) -> t.Dict[int, t.Dict[str, str]]:
        """Get signals for content IDs, searching across all banks."""
        remaining = set(id)
        if not remaining:
            return {}
        result: t.Dict[int, t.Dict[str, str]] = {}
        all_banks = self.get_banks()
        for bank_name in all_banks:
            if not remaining:
                break
            with self._open_bank_content(bank_name) as db:
                for content_id in list(remaining):
                    raw = db.get(_content_key(content_id))
                    if raw is not None:
                        stored = dataclass_json.dataclass_loads(
                            raw.decode(), _BankStoredContent
                        )
                        result[content_id] = dict(stored.signals)
                        remaining.discard(content_id)
        return result

    def bank_content_update(self, val: iface.BankContentConfig) -> None:
        """Update content metadata, preserving created_ts and signals."""
        with self._open_bank_content(val.bank.name) as db:
            existing_raw = db.get(_content_key(val.id))
            if existing_raw is None:
                raise KeyError(f"No bank content with ID {val.id}")
            existing = dataclass_json.dataclass_loads(
                existing_raw.decode(), _BankStoredContent
            )
            updated = _BankStoredContent(
                id=val.id,
                disable_until_ts=val.disable_until_ts,
                collab_metadata={k: list(v) for k, v in val.collab_metadata.items()},
                original_media_uri=val.original_media_uri,
                created_ts=existing.created_ts,
                signals=existing.signals,
            )
            db[_content_key(val.id)] = dataclass_json.dataclass_dumps(updated).encode()

    def bank_add_content(
        self,
        bank_name: str,
        content_signals: t.Dict[t.Type[SignalType], str],
        config: t.Optional[iface.BankContentConfig] = None,
    ) -> int:
        """Add content to a bank and return the new globally unique content ID."""
        if self.get_bank(bank_name) is None:
            raise KeyError(f"No such bank: {bank_name!r}")
        content_id = self._get_next_id()
        now = int(time.time())
        stored = _BankStoredContent(
            id=content_id,
            disable_until_ts=iface.BankContentConfig.ENABLED,
            collab_metadata={},
            original_media_uri=None,
            created_ts=now,
            signals={st.get_name(): val for st, val in content_signals.items()},
        )
        if config is not None:
            stored.disable_until_ts = config.disable_until_ts
            stored.collab_metadata = {
                k: list(v) for k, v in config.collab_metadata.items()
            }
            stored.original_media_uri = config.original_media_uri
        with self._open_bank_content(bank_name) as db:
            db[_content_key(content_id)] = dataclass_json.dataclass_dumps(
                stored
            ).encode()
        return content_id

    def bank_remove_content(self, bank_name: str, content_id: int) -> int:
        """Remove content from a bank by ID. Returns 1 if removed, 0 if not found."""
        with self._open_bank_content(bank_name) as db:
            key = _content_key(content_id)
            if key in db:
                del db[key]
                return 1
        return 0

    def get_current_index_build_target(
        self, signal_type: t.Type[SignalType]
    ) -> iface.SignalTypeIndexBuildCheckpoint:
        """Scan all bank content to compute the current index build target."""
        signal_type_name = signal_type.get_name()
        total_hash_count = 0
        last_item_timestamp = -1
        last_item_id = -1
        for bank_name in self.get_banks():
            with self._open_bank_content(bank_name) as db:
                for raw_key in db.keys():
                    raw = db[raw_key]
                    stored = dataclass_json.dataclass_loads(
                        raw.decode(), _BankStoredContent
                    )
                    if signal_type_name not in stored.signals:
                        continue
                    total_hash_count += 1
                    if stored.created_ts > last_item_timestamp or (
                        stored.created_ts == last_item_timestamp
                        and stored.id > last_item_id
                    ):
                        last_item_timestamp = stored.created_ts
                        last_item_id = stored.id
        if total_hash_count == 0:
            return iface.SignalTypeIndexBuildCheckpoint.get_empty()
        return iface.SignalTypeIndexBuildCheckpoint(
            last_item_timestamp=last_item_timestamp,
            last_item_id=last_item_id,
            total_hash_count=total_hash_count,
        )

    def bank_yield_content(
        self,
        signal_type: t.Optional[t.Type[SignalType]] = None,
        batch_size: int = 100,
    ) -> t.Iterator[iface.BankContentIterationItem]:
        """Yield all bank content, optionally filtered to a specific signal type."""
        signal_type_name = signal_type.get_name() if signal_type is not None else None
        for bank_name in self.get_banks():
            with self._open_bank_content(bank_name) as db:
                for raw_key in db.keys():
                    raw = db[raw_key]
                    stored = dataclass_json.dataclass_loads(
                        raw.decode(), _BankStoredContent
                    )
                    for stype_name, signal_val in stored.signals.items():
                        if (
                            signal_type_name is not None
                            and stype_name != signal_type_name
                        ):
                            continue
                        yield iface.BankContentIterationItem(
                            signal_type_name=stype_name,
                            signal_val=signal_val,
                            bank_content_id=stored.id,
                            bank_content_timestamp=stored.created_ts,
                        )
