# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Simple dbm implementation of the storage interface.
"""

import dbm
import functools
import logging
from enum import Enum
import os
import tempfile
from dataclasses import dataclass
import json
import time
import typing as t
from pathlib import Path

from threatexchange.utils import dataclass_json
from threatexchange.storage import interfaces as iface
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.signal_type.index import SignalTypeIndex
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

"""
Version of the on-disk layout written by DBMStore.

Bump this whenever the layout changes incompatibly.
"""
STATE_VERSION = 1


"""
Plain text file (outside of any dbm) in the store folder holding STATE_VERSION.

It's plain text so it can be checked without opening (and therefore creating)
any dbm file, and regardless of which dbm backend wrote the store.
"""
STATE_VERSION_FILENAME = "state_version"


"""
Folder in the store folder holding one serialized
SignalTypeIndex file per SignalType, written via SignalTypeIndex.serialize.

Indices can be large, so they live in plain files rather than in a dbm.
The "_v2" suffix avoids colliding with the legacy CLI's "index/" folder.
"""
INDEX_FOLDER_NAME = "index_v2"


class _DbType(Enum):
    """
    The dbm files (or directories of dbm files) in the store folder.
    """

    SIGNAL_TYPE = "signal_type"
    CONTENT_TYPE = "content_type"
    EXCHANGE_TYPE = "exchange_type"
    EXCHANGES = "exchanges"
    EXCHANGE_STATUS = "exchange_status"
    EXCHANGE_DATA = "exchange_data"
    BANKS = "banks"
    INDEX_CHECKPOINT = "index_checkpoint"
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
    # concrete types for JSON roundtrip
    collab_metadata: t.Dict[str, t.List[str]]
    original_media_uri: t.Optional[str]
    created_ts: int  # set at insert, preserved on update; used for index checkpoint
    signals: t.Dict[str, str]  # signal_type_name -> signal_value


@dataclass
class _ExchangeDataRecord:
    """
    Stored fetched record for one key of a collab, plus its bank content link.

    bank_content_id points at the content in the collab's bank that was
    created from this record, or None if the record had no usable signals.
    """

    value_json: str  # dataclass_dumps of the API's record value class
    bank_content_id: t.Optional[int] = None


def record_key_to_str(key: t.Any) -> str:
    """
    Convert a TUpdateRecordKey to a stable string.

    This is how keys are stored in DBM, and also the form used for
    BankContentConfig.collab_metadata. Reverse with record_key_from_str.
    """
    if isinstance(key, tuple):
        return json.dumps(list(key))
    return json.dumps(key)


def record_key_from_str(key_str: str) -> t.Any:
    """Reverse of record_key_to_str (JSON lists become tuples)."""

    def _to_tuples(val: t.Any) -> t.Any:
        if isinstance(val, list):
            return tuple(_to_tuples(v) for v in val)
        return val

    return _to_tuples(json.loads(key_str))


_DBM_FILE_SUFFIXES = ("", ".db", ".dir", ".dat", ".bak")


def _clear_data(path: Path) -> None:
    """
    Delete all records in the dbm at path, leaving an empty db.

    Opening with flag "n" always creates a new, empty db, replacing any
    existing one.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    dbm.open(str(path), "n").close()


_NEXT_ID_KEY = b"__next_id__"


def _iter_dbm_items(
    open_db: t.Callable[[], t.Any], batch_size: int = 100
) -> t.Iterator[t.Tuple[bytes, bytes]]:
    """
    Iterate a dbm's items without holding it open while yielding.

    Some dbm backends (e.g. dbm.gnu) take an exclusive lock, so a generator
    that yields with the db open would make any store call by the caller
    that reopens the same file fail. Instead, snapshot the keys, then read
    values in batches, closing the db before yielding each batch. Keys
    deleted mid-iteration are skipped.

    Note: for backends other than dbm.gnu, this loads every key into memory
    up front, which may not be ideal for large dbs. The generic dbm interface
    has no ordered or resumable iteration, so avoiding this likely needs a
    different backend. dbm.gnu can resume iteration from a key, so it uses
    _iter_gdbm_items instead, which only holds one batch in memory.
    """
    batch_size = max(batch_size, 1)
    with open_db() as db:
        if hasattr(db, "nextkey"):
            keys = None
        else:
            keys = list(db.keys())
    if keys is None:
        yield from _iter_gdbm_items(open_db, batch_size)
        return
    for i in range(0, len(keys), batch_size):
        with open_db() as db:
            batch = [(k, db.get(k)) for k in keys[i : i + batch_size]]
        for k, v in batch:
            if v is not None:
                yield k, v


def _iter_gdbm_items(
    open_db: t.Callable[[], t.Any], batch_size: int
) -> t.Iterator[t.Tuple[bytes, bytes]]:
    """
    Iterate a dbm.gnu db's items, holding only one batch in memory.

    Like _iter_dbm_items, the db is closed before yielding each batch. Each
    batch resumes with nextkey() from the last key read, which gdbm supports
    across a close and reopen.

    The order is gdbm's hash order, not sorted. If the db is written to while
    iterating, gdbm may reorganize its buckets, so keys can be skipped or
    repeated. If the last key of a batch is deleted while iterating, there is
    nothing to resume from, so this raises rather than silently stopping.
    """
    last: t.Optional[bytes] = None
    while True:
        batch: t.List[t.Tuple[bytes, bytes]] = []
        with open_db() as db:
            if last is None:
                key = db.firstkey()
            elif last not in db:
                raise RuntimeError(
                    f"Key {last!r} was deleted mid-iteration, can't resume"
                )
            else:
                key = db.nextkey(last)
            while key is not None and len(batch) < batch_size:
                batch.append((key, db[key]))
                key = db.nextkey(key)
        yield from batch
        if key is None:
            return
        last = batch[-1][0]


def _content_key(content_id: int) -> str:
    """Key for a bank content record in the per-bank DBM."""
    return str(content_id)


class DBMStore(iface.IUnifiedStore):
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

        stored_version = self.read_state_version(folder)
        if stored_version is not None and stored_version > STATE_VERSION:
            raise ValueError(
                f"{folder} was written by a newer version of this library "
                f"(state version {stored_version}, this version supports up to "
                f"{STATE_VERSION}). Upgrade, or use a fresh folder."
            )

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

    @staticmethod
    def read_state_version(folder: Path) -> t.Optional[int]:
        """
        Return the state version stored in folder, or None if there isn't one.

        Doesn't open or create any dbm files, so it's safe to call before
        deciding whether a folder needs migrating.
        """
        version_file = folder / STATE_VERSION_FILENAME
        if not version_file.is_file():
            return None
        content = version_file.read_text().strip()
        try:
            return int(content)
        except ValueError:
            raise ValueError(
                f"Unparsable {STATE_VERSION_FILENAME} in {folder}: {content!r}"
            ) from None

    def _open(self, db: _DbType, *, sub_db: str = ""):
        file = self._folder / db.value
        if sub_db:
            file = file / sub_db
        return dbm.open(str(file), "c")

    def _open_collab_data(self, collab_name: str):
        """Open a per-collab exchange data db in its own subfolder."""
        d = self._folder / _DbType.EXCHANGE_DATA.value
        d.mkdir(exist_ok=True)
        return dbm.open(str(d / collab_name), "c")

    def _open_bank_content(self, bank_name: str):
        """Open the per-bank content DBM file, creating the directory if needed."""
        d = self._folder / _DbType.BANK_CONTENT.value
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

    # ISignalTypeIndexStore

    def _index_file(self, signal_type: t.Type[SignalType]) -> Path:
        return self._folder / INDEX_FOLDER_NAME / f"{signal_type.get_name()}.index"

    def get_signal_type_index(
        self, signal_type: t.Type[SignalType]
    ) -> t.Optional[SignalTypeIndex[int]]:
        """Return the stored index for this SignalType, if one has been stored."""
        path = self._index_file(signal_type)
        if not path.is_file():
            return None
        with path.open("rb") as f:
            return signal_type.get_index_cls().deserialize(f)

    def store_signal_type_index(
        self,
        signal_type: t.Type[SignalType],
        index: SignalTypeIndex,
        checkpoint: iface.SignalTypeIndexBuildCheckpoint,
    ) -> None:
        """
        Persist the index to its file, then record its build checkpoint.

        The index is written to a temporary file and moved into place, so a
        failed write leaves any previously stored index intact.
        """
        path = self._index_file(signal_type)
        path.parent.mkdir(exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "wb") as f:
                index.serialize(f)
                # Make sure the data is on disk before the rename, so a crash
                # can't leave a partial file under the final name.
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_name, path)
        except BaseException:
            Path(tmp_name).unlink(missing_ok=True)
            raise
        with self._open(_DbType.INDEX_CHECKPOINT) as db:
            db[signal_type.get_name()] = dataclass_json.dataclass_dumps(
                checkpoint
            ).encode()

    def get_last_index_build_checkpoint(
        self, signal_type: t.Type[SignalType]
    ) -> t.Optional[iface.SignalTypeIndexBuildCheckpoint]:
        """
        Return the checkpoint of the stored index, or None if there isn't one.

        Returns None if the index file is missing, even if a checkpoint was
        recorded, so callers rebuild rather than trust a checkpoint for an
        index that can't be loaded.
        """
        if not self._index_file(signal_type).is_file():
            return None
        with self._open(_DbType.INDEX_CHECKPOINT) as db:
            raw = db.get(signal_type.get_name())
        if raw is None:
            return None
        return dataclass_json.dataclass_loads(
            raw.decode(), iface.SignalTypeIndexBuildCheckpoint
        )

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
        """
        Create or update a collaboration.

        Setup happens in order, and teardown (_exchange_teardown) in reverse:
          1. The exchange config
          2. The collab's bank, named after the collab
          3. Fetch status and fetched data, created lazily on first fetch

        If creating the bank fails, the config is kept. The bank is created
        again by _ensure_collab_bank on the next fetch (and should be by
        anything that rebuilds banks, like the dataset command).
        """
        if create and self.get_bank(cfg.name) is not None:
            raise ValueError(
                f"Can't create collaboration {cfg.name!r}, "
                "a bank with that name already exists"
            )
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
        if create:
            self._ensure_collab_bank(cfg.name)

    def _ensure_collab_bank(self, collab_name: str) -> None:
        """
        Create the bank holding a collab's fetched content, if missing.

        Like HMA, each collab gets one bank, named after the collab.
        Safe to call repeatedly, so it can regenerate a missing bank.
        """
        if self.get_bank(collab_name) is None:
            self.bank_update(
                iface.BankConfig(name=collab_name, matching_enabled_ratio=1.0),
                create=True,
            )

    def _exchange_teardown(self, name: str, *, keep_config: bool) -> None:
        """
        Tear down a collab in the reverse order of setup (see exchange_update).

          3. Fetch status, then fetched data. The status holds the checkpoint,
             so it goes first: if interrupted, the next fetch starts over
             rather than resuming on top of missing data.
          2. The bank (if keep_config, only its content is cleared)
          1. The exchange config (unless keep_config)
        """
        with self._open(_DbType.EXCHANGE_STATUS) as db:
            if name in db:
                del db[name]
        _clear_data(self._folder / _DbType.EXCHANGE_DATA.value / name)
        if keep_config:
            _clear_data(self._folder / _DbType.BANK_CONTENT.value / name)
            return
        self.bank_delete(name)
        with self._open(_DbType.EXCHANGES) as db:
            if name in db:
                del db[name]

    def exchange_delete(self, name: str) -> None:
        """Delete a collaboration and all its associated data, including its bank."""
        self._exchange_teardown(name, keep_config=False)

    def exchange_clear_data(self, name: str) -> None:
        """
        Drop all fetched data for a collab, but keep its config.

        Clears the fetched records, fetch status (including the checkpoint),
        and the collab's bank content, so the next fetch starts from scratch.

        Not part of the ISignalExchangeStore interface.
        """
        if self.exchange_get(name) is None:
            raise KeyError(f"No such collaboration: {name!r}")
        self._exchange_teardown(name, keep_config=True)

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
        """
        Get the last fetch status.

        The status is created lazily by the first fetch, so a collab that
        has never been fetched gets a default status.
        """
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
        """Record the start of a fetch attempt, creating the status if missing."""
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

    def _exchange_api_cls(self, collab_name: str) -> TSignalExchangeAPICls:
        """Return the API class for a stored collab, or raise KeyError."""
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
        return api_cls

    def _record_to_signals(
        self,
        api_cls: TSignalExchangeAPICls,
        collab: CollaborationConfigBase,
        key: t.Any,
        val: t.Any,
    ) -> t.Dict[str, str]:
        """
        Convert one fetched record to the signals for its bank content.

        Bank content holds one signal per SignalType, so if a record has
        several signals of the same type, the lowest one is kept.
        """
        converted = api_cls.naive_convert_to_signal_type(
            list(self.signal_types.values()), collab, {key: val}
        )
        ret = {}
        for st, signals in converted.items():
            if not signals:
                continue
            ordered = sorted(signals)
            if len(ordered) > 1:
                logging.warning(
                    "%s record %r has %d %s signals, only keeping one",
                    collab.name,
                    key,
                    len(ordered),
                    st.get_name(),
                )
            ret[st.get_name()] = ordered[0]
        return ret

    def _sync_record_bank_content(
        self,
        bank_db: t.Any,
        collab_name: str,
        key: t.Any,
        content_id: t.Optional[int],
        signals: t.Dict[str, str],
        now: int,
    ) -> t.Optional[int]:
        """
        Make a record's bank content match its signals, return its content id.

        Removes the content if there are no signals, creates it if there is
        none yet, and updates it in place (keeping its id) if they changed.
        """
        stored = None
        if content_id is not None:
            raw = bank_db.get(_content_key(content_id))
            if raw is not None:
                stored = dataclass_json.dataclass_loads(
                    raw.decode(), _BankStoredContent
                )
        if not signals:
            if stored is not None:
                del bank_db[_content_key(stored.id)]
            return None
        if stored is None:
            stored = _BankStoredContent(
                id=self._get_next_id(),
                disable_until_ts=iface.BankContentConfig.ENABLED,
                collab_metadata={collab_name: [record_key_to_str(key)]},
                original_media_uri=None,
                created_ts=now,
                signals=signals,
            )
        elif stored.signals == signals:
            return stored.id
        else:
            stored.signals = signals
            # Bump created_ts so incremental index builds see the change
            stored.created_ts = now
        bank_db[_content_key(stored.id)] = dataclass_json.dataclass_dumps(
            stored
        ).encode()
        return stored.id

    def exchange_commit_fetch(
        self,
        collab: CollaborationConfigBase,
        old_checkpoint: t.Optional[FetchCheckpointBase],
        dat: t.Dict[t.Any, t.Any],
        checkpoint: FetchCheckpointBase,
    ) -> None:
        """
        Commit fetched data and update the checkpoint.

        Each update is merged with the stored record via the API's
        fetch_value_merge. The collab's bank is kept in sync: one bank
        content per record with usable signals, whose collab_metadata
        points back at the record key.
        """
        api_cls = self._exchange_api_cls(collab.name)
        record_cls = api_cls.get_record_cls()
        self._ensure_collab_bank(collab.name)
        now = int(time.time())
        with (
            self._open_collab_data(collab.name) as data_db,
            self._open_bank_content(collab.name) as bank_db,
        ):
            for key, val in dat.items():
                db_key = record_key_to_str(key).encode()
                raw_existing = data_db.get(db_key)
                existing = None
                old_val = None
                if raw_existing is not None:
                    existing = dataclass_json.dataclass_loads(
                        raw_existing.decode(), _ExchangeDataRecord
                    )
                    old_val = dataclass_json.dataclass_loads(
                        existing.value_json, record_cls
                    )
                merged = api_cls.fetch_value_merge(old_val, val)
                content_id = None if existing is None else existing.bank_content_id

                signals: t.Dict[str, str] = {}
                if merged is not None:
                    signals = self._record_to_signals(api_cls, collab, key, merged)

                content_id = self._sync_record_bank_content(
                    bank_db, collab.name, key, content_id, signals, now
                )

                # Sync the record itself
                if merged is None:
                    if db_key in data_db:
                        del data_db[db_key]
                else:
                    data_db[db_key] = dataclass_json.dataclass_dumps(
                        _ExchangeDataRecord(
                            value_json=dataclass_json.dataclass_dumps(merged),
                            bank_content_id=content_id,
                        )
                    ).encode()
        with self._open(_DbType.EXCHANGE_STATUS) as db:
            raw = db.get(collab.name)
            status = (
                dataclass_json.dataclass_loads(raw.decode(), _ExchangeStatus)
                if raw is not None
                else _ExchangeStatus()
            )
            status.checkpoint_json = dataclass_json.dataclass_dumps(checkpoint)
            ts = checkpoint.get_progress_timestamp()
            status.checkpoint_ts = ts if ts is not None else now
            db[collab.name] = dataclass_json.dataclass_dumps(status).encode()

    def exchange_get_data(
        self,
        collab_name: str,
        key: TUpdateRecordKey,
    ) -> iface.FetchedSignalMetadata:
        """Return the stored metadata for a fetched record."""
        record_cls = self._exchange_api_cls(collab_name).get_record_cls()
        with self._open_collab_data(collab_name) as db:
            raw = db.get(record_key_to_str(key).encode())
        if raw is None:
            raise KeyError(f"No data for key {key!r} in collaboration {collab_name!r}")
        record = dataclass_json.dataclass_loads(raw.decode(), _ExchangeDataRecord)
        return dataclass_json.dataclass_loads(record.value_json, record_cls)

    def exchange_yield_data(
        self, collab_name: str
    ) -> t.Iterator[t.Tuple[t.Any, t.Any]]:
        """
        Yield every stored (key, record) for a collab, in no particular order.

        Not part of the ISignalExchangeStore interface.
        """
        record_cls = self._exchange_api_cls(collab_name).get_record_cls()
        for raw_key, raw in _iter_dbm_items(
            lambda: self._open_collab_data(collab_name)
        ):
            record = dataclass_json.dataclass_loads(raw.decode(), _ExchangeDataRecord)
            yield (
                record_key_from_str(raw_key.decode()),
                dataclass_json.dataclass_loads(record.value_json, record_cls),
            )

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
            d = self._folder / _DbType.BANK_CONTENT.value
            old_base = d / rename_from
            new_base = d / bank.name
            for ext in _DBM_FILE_SUFFIXES:
                old = old_base.with_name(old_base.name + ext)
                new = new_base.with_name(new_base.name + ext)
                if old.exists():
                    old.rename(new)

    def bank_delete(self, name: str) -> None:
        """
        Delete a bank and all its content. No exception if bank doesn't exist.

        Content is cleared before the bank config, the reverse of creation.
        """
        _clear_data(self._folder / _DbType.BANK_CONTENT.value / name)
        with self._open(_DbType.BANKS) as db:
            key = name.encode() if not isinstance(name, bytes) else name
            if key in db:
                del db[key]

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
            for _, raw in _iter_dbm_items(
                functools.partial(self._open_bank_content, bank_name), batch_size
            ):
                stored = dataclass_json.dataclass_loads(
                    raw.decode(), _BankStoredContent
                )
                for stype_name, signal_val in stored.signals.items():
                    if signal_type_name is not None and stype_name != signal_type_name:
                        continue
                    yield iface.BankContentIterationItem(
                        signal_type_name=stype_name,
                        signal_val=signal_val,
                        bank_content_id=stored.id,
                        bank_content_timestamp=stored.created_ts,
                    )
