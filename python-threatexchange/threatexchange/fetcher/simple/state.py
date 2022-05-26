# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved


from dataclasses import dataclass, field
import logging
import typing as t
from threatexchange.fetcher.fetch_api import (
    TSignalExchangeAPICls,
)

from threatexchange.signal_type.signal_base import SignalType
from threatexchange.fetcher import fetch_state
from threatexchange.fetcher.collab_config import CollaborationConfigBase

K = t.TypeVar("K")
V = t.TypeVar("V")

# Fill out sensible defaults for mypy. T_ to avoid confusing with TFetchDelta
T_FetchDelta = fetch_state.FetchDelta[
    fetch_state.FetchCheckpointBase, fetch_state.FetchedSignalMetadata
]


@dataclass
class SimpleFetchedSignalMetadata(fetch_state.FetchedSignalMetadata):
    """
    Simple dataclass for fetched data.

    Merge by addition rather than replacement.
    """

    opinions: t.List[fetch_state.SignalOpinion] = field(default_factory=list)

    def get_as_opinions(self) -> t.List[fetch_state.SignalOpinion]:
        return self.opinions

    @classmethod
    def merge(
        cls, older: "SimpleFetchedSignalMetadata", newer: "SimpleFetchedSignalMetadata"
    ) -> "SimpleFetchedSignalMetadata":
        if not older.opinions:
            return newer

        by_owner = {o.owner: o for o in newer.opinions}
        return cls([by_owner.get(o.owner, o) for o in older.opinions])

    @classmethod
    def get_trivial(cls):
        return cls([fetch_state.SignalOpinion.get_trivial()])


@dataclass
class FetchDeltaWithUpdateStream(
    fetch_state.FetchDelta[
        fetch_state.TFetchCheckpoint, fetch_state.TFetchedSignalMetadata
    ],
    t.Generic[fetch_state.TFetchCheckpoint, fetch_state.TFetchedSignalMetadata, K, V],
):
    """
    TODO
    """

    update_record: t.Dict[K, t.Optional[V]]
    checkpoint: fetch_state.TFetchCheckpoint
    done: bool

    @classmethod
    def _merge_update(cls, old_v: V, new_v: V) -> t.Optional[V]:
        """
        How to merge updates.

        By default, assume newer replaces older. Another strategy might be
        merging records together.
        """
        return new_v

    def merge(
        self: "FetchDeltaWithUpdateStream", newer: "FetchDeltaWithUpdateStream"
    ) -> None:
        updates = newer.update_record
        if not updates:
            return

        for k, new_v in updates.items():
            old_v = self.update_record.get(k)
            result_v: t.Optional[V] = new_v
            if None not in (old_v, new_v):
                result_v = self._merge_update(old_v, new_v)
            if result_v is None:
                self.update_record.pop(k, None)
            else:
                self.update_record[k] = result_v
        self.checkpoint = newer.checkpoint
        self.done = newer.done

    def record_count(self) -> int:
        return len(self.update_record)

    def next_checkpoint(self) -> fetch_state.TFetchCheckpoint:
        return self.checkpoint

    def has_more(self) -> bool:
        return not self.done


class SimpleFetchDelta(
    FetchDeltaWithUpdateStream[
        fetch_state.TFetchCheckpoint,
        fetch_state.TFetchedSignalMetadata,
        t.Tuple[str, str],
        fetch_state.TFetchedSignalMetadata,
    ],
):
    """
    If the update stream is already stored as signal types, no conversion is needed.
    """

    def get_for_signal_type(
        self, signal_type: t.Type[SignalType]
    ) -> t.Dict[str, fetch_state.TFetchedSignalMetadata]:
        type_str = signal_type.get_name()
        return {
            signal_str: meta
            for (signal_type_str, signal_str), meta in self.update_record.items()
            if signal_type_str == type_str and meta is not None
        }


@dataclass
class _StateTracker:
    _delta: t.Optional[T_FetchDelta]
    dirty: bool = False

    def merge(self, new_delta: T_FetchDelta) -> None:
        if not self._delta:
            self._delta = new_delta
        else:
            self._delta.merge(new_delta)
        self.dirty = True

    @property
    def empty(self) -> bool:
        return self._delta is None

    @property
    def delta(self) -> T_FetchDelta:
        assert self._delta is not None
        return self._delta

    @property
    def checkpoint(self) -> t.Optional[fetch_state.FetchCheckpointBase]:
        return None if self._delta is None else self._delta.next_checkpoint()


class SimpleFetchedStateStore(fetch_state.FetchedStateStoreBase):
    """
    TODO
    """

    def __init__(
        self,
        api_cls: TSignalExchangeAPICls,
    ) -> None:
        self.api_cls = api_cls
        self._state: t.Dict[str, _StateTracker] = {}

    def _read_state(
        self,
        collab_name: str,
    ) -> t.Optional[T_FetchDelta]:
        raise NotImplementedError

    def _write_state(self, collab_name: str, delta: T_FetchDelta) -> None:
        raise NotImplementedError

    def get_checkpoint(
        self, collab: CollaborationConfigBase
    ) -> t.Optional[fetch_state.FetchCheckpointBase]:
        return self._get_state(collab.name).checkpoint

    def _get_state(self, collab_name: str) -> _StateTracker:
        if collab_name not in self._state:
            logging.debug("Loading state for %s", collab_name)
            delta = self._read_state(collab_name)
            self._state[collab_name] = _StateTracker(delta)
        return self._state[collab_name]

    def merge(
        self,
        collab: CollaborationConfigBase,
        delta: T_FetchDelta,
    ) -> None:
        """
        Merge a FetchDeltaBase into the state.

        At the implementation's discretion, it may call flush() or the
        equivalent work.
        """

        state = self._get_state(collab.name)

        if delta.record_count() == 0 and delta.next_checkpoint() in (
            None,
            state.checkpoint,
        ):
            logging.warning("No op update for %s", collab.name)
            return

        state.merge(delta)

    def flush(self):
        for collab_name, state in self._state.items():
            if state.dirty:
                assert state.delta is not None
                self._write_state(collab_name, state.delta)
                state.dirty = False

    def get_for_signal_type(
        self, collabs: t.List[CollaborationConfigBase], signal_type: t.Type[SignalType]
    ) -> t.Dict[str, t.Dict[str, fetch_state.FetchedSignalMetadata]]:
        ret = {}
        for collab in collabs:
            state = self._get_state(collab.name)
            if not state.empty:
                ret[collab.name] = state.delta.get_for_signal_type(signal_type)
        return ret
