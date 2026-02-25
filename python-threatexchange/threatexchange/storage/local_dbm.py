# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Simple dbm implementation of the storage interface.
"""

import dbm
from enum import Enum
from dataclasses import dataclass
import typing as t
from pathlib import Path

from threatexchange.utils import dataclass_json
from threatexchange.storage import interfaces as iface
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.content_type.content_base import ContentType
from threatexchange.exchanges.signal_exchange_api import TSignalExchangeAPICls
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
    BANKS = "banks"
    INDEX = "index"


@dataclass
class _SignalTypeCfg:
    enabled_ratio: float = 1.0


# TODO - eventually to unified store
class DBMStore(iface.ISignalTypeConfigStore):
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
