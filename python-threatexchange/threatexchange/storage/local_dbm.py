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

    checkpoint_json: t.Optional[str] = None  # dataclass_dumps of FetchCheckpointBase subclass
    checkpoint_ts: t.Optional[int] = None
    running_fetch_start_ts: t.Optional[int] = None
    last_fetch_complete_ts: t.Optional[int] = None
    last_fetch_succeeded: t.Optional[bool] = None
    up_to_date: bool = False


@dataclass
class _ExchangeAPICredsCfg:
    """Stored API-level credentials: JSON-serialized CredentialHelper subclass."""

    credentials_json: t.Optional[str] = None  # dataclass_dumps of CredentialHelper subclass


def _key_str(key: t.Any) -> str:
    """Convert a TUpdateRecordKey to a stable string for DBM storage."""
    if isinstance(key, tuple):
        return json.dumps(list(key))
    return json.dumps(key)


# TODO - eventually to unified store
class DBMStore(
    iface.ISignalTypeConfigStore,
    iface.IContentTypeConfigStore,
    iface.ISignalExchangeStore,
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

    def exchange_apis_get_configs(self) -> t.Mapping[str, iface.SignalExchangeAPIConfig]:
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
        with self._open_collab_data(name) as db:
            for k in list(db.keys()):
                del db[k]

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
        dat: t.Dict[str, t.Any],
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
                raise KeyError(f"No data for key {key!r} in collaboration {collab_name!r}")
            return dataclass_json.dataclass_loads(raw.decode(), record_cls)
