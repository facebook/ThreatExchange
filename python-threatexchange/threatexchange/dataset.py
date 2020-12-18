#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
A wrapper around fetching, storing, and recovering the state from TE.
"""

import json
import pathlib
import typing as t

from . import TE, collab_config
from .content_type import meta
from .signal_type import signal_base


class FetchCheckpoint(t.NamedTuple):
    last_full_fetch: float
    last_fetch: float

    def next(self, fetch_start_time: float, full_fetch: bool) -> "FetchCheckpoint":
        full_fetch = full_fetch or not self.last_full_fetch
        return FetchCheckpoint(
            fetch_start_time if full_fetch else self.last_full_fetch, fetch_start_time
        )

    def serialize(self) -> str:
        return f"{self.last_full_fetch} {self.last_fetch}"

    @classmethod
    def deserialize(cls, s: str) -> "FetchCheckpoint":
        last_full, _, last = s.partition(" ")
        return cls(float(last_full), float(last))


class Dataset:

    EXTENSION = ".te"

    def __init__(
        self,
        config: collab_config.CollaborationConfig,
        state_dir: t.Optional[pathlib.Path] = None,
    ) -> None:
        self.config = config
        if state_dir is None:
            state_dir = pathlib.Path.home() / config.default_state_dir_name
            assert not state_dir.is_file()
        self.state_dir = state_dir

    @property
    def is_cache_empty(self) -> bool:
        return not (
            self.state_dir.exists() and any(self.state_dir.glob(f"*{self.EXTENSION}"))
        )

    def _fetch_checkpoint_path(self) -> pathlib.Path:
        return self.state_dir / f"fetch_checkpoint{self.EXTENSION}"

    def _indicator_checkpoint_path(self, privacy_group: int) -> pathlib.Path:
        return (
            self.state_dir / f"indicators/{privacy_group}/_checkpoint{self.EXTENSION}"
        )

    def clear_cache(self) -> None:
        for p in self.state_dir.iterdir():
            if p.suffix == self.EXTENSION:
                p.unlink()

    def record_fetch_checkpoint(
        self, fetch_started_timestamp: float, full_fetch: bool
    ) -> None:
        prev = self.get_fetch_checkpoint()
        with self._fetch_checkpoint_path().open("w+") as f:
            f.write(prev.next(fetch_started_timestamp, full_fetch).serialize())

    def get_fetch_checkpoint(self) -> FetchCheckpoint:
        checkpoint = self._fetch_checkpoint_path()
        if not checkpoint.exists():
            return FetchCheckpoint(0, 0)
        return FetchCheckpoint.deserialize(checkpoint.read_text())

    def get_indicator_checkpoint(self, privacy_group) -> t.Dict:
        checkpoint = {
            "last_stop_time": 0,
            "last_run_time": 0,
            "types": None,
        }
        checkpoint_file = self._indicator_checkpoint_path(privacy_group)
        if not checkpoint_file.exists():
            return checkpoint
        with checkpoint_file.open("r+") as f:
            checkpoint = json.load(f)
        return checkpoint

    def set_indicator_checkpoint(
        self,
        privacy_group: int,
        stop_time: int,
        request_time: int,
        types: t.List = None,
    ) -> None:
        checkpoint = {
            "last_stop_time": stop_time,
            "last_run_time": request_time,
            "types": types,
        }
        with self._indicator_checkpoint_path(privacy_group).open("w+") as f:
            json.dump(checkpoint, f)

    def _signal_state_file(self, signal_type: signal_base.SignalType) -> pathlib.Path:
        return self.state_dir / f"{signal_type.get_name()}{self.EXTENSION}"

    def get_indicator_store(self, privacy_group: int) -> signal_base.IndicatorSignals:
        return signal_base.IndicatorSignals(self.state_dir, privacy_group)

    def load_cache(
        self, signal_types: t.Optional[t.Iterable[signal_base.SignalType]] = None
    ) -> t.List[signal_base.SignalType]:
        """Load everything in the state directory and initialize signal types"""
        if signal_types is None:
            signal_types = [s() for s in meta.get_all_signal_types()]
        ret = []
        for signal_type in signal_types:
            signal_state_file = self._signal_state_file(signal_type)
            if signal_state_file.exists():
                signal_type.load(signal_state_file)
            ret.append(signal_type)
        return ret

    def load_indicator_cache(
        self, indicator_signals: signal_base.IndicatorSignals
    ) -> None:
        """Load indicator files"""
        indicator_signals.load_indicators()

    def store_cache(self, signal_type: signal_base.SignalType) -> None:
        if not self.state_dir.exists():
            self.state_dir.mkdir()
        signal_type.store(self._signal_state_file(signal_type))

    def store_indicator_cache(
        self, indicator_signals: signal_base.IndicatorSignals
    ) -> None:
        if not self.state_dir.exists():
            self.state_dir.mkdir()
        indicator_signals.store_indicators()
