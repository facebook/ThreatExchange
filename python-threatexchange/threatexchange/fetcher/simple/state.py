# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved


from dataclasses import dataclass, field
import logging
import typing as t
from threatexchange.fetcher.fetch_api import (
    SignalExchangeAPI,
    TSignalExchangeAPI,
    TSignalExchangeAPICls,
)

from threatexchange.signal_type.signal_base import SignalType
from threatexchange.fetcher import fetch_state
from threatexchange.fetcher.collab_config import CollaborationConfigBase

K = t.TypeVar("K")
V = t.TypeVar("V")


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
    def get_trivial(cls):
        return cls([fetch_state.SignalOpinion.get_trivial()])


# @dataclass
# class FetchDeltaWithUpdateStream(
#     fetch_state.FetchDelta[
#         fetch_state.TFetchCheckpoint, fetch_state.TFetchedSignalMetadata
#     ],
#     t.Generic[fetch_state.TFetchCheckpoint, fetch_state.TFetchedSignalMetadata, K, V],
# ):
#     """
#     TODO
#     """

#     update_record: t.Dict[K, t.Optional[V]]
#     checkpoint: fetch_state.TFetchCheckpoint

#     @classmethod
#     def _merge_update(cls, old_v: V, new_v: V) -> t.Optional[V]:
#         """
#         How to merge updates.

#         By default, assume newer replaces older. Another strategy might be
#         merging records together.
#         """
#         return new_v

#     def merge(
#         self: "FetchDeltaWithUpdateStream", newer: "FetchDeltaWithUpdateStream"
#     ) -> None:
#         updates = newer.update_record
#         if not updates:
#             return

#         for k, new_v in updates.items():
#             old_v = self.update_record.get(k)
#             result_v: t.Optional[V] = new_v
#             if None not in (old_v, new_v):
#                 result_v = self._merge_update(old_v, new_v)
#             if result_v is None:
#                 self.update_record.pop(k, None)
#             else:
#                 self.update_record[k] = result_v
#         self.checkpoint = newer.checkpoint

#     def record_count(self) -> int:
#         return len(self.update_record)

#     def next_checkpoint(self) -> fetch_state.TFetchCheckpoint:
#         return self.checkpoint


# class SimpleFetchDelta(
#     FetchDeltaWithUpdateStream[
#         fetch_state.TFetchCheckpoint,
#         fetch_state.TFetchedSignalMetadata,
#         t.Tuple[str, str],
#         fetch_state.TFetchedSignalMetadata,
#     ],
# ):
#     """
#     If the update stream is already stored as signal types, no conversion is needed.
#     """

#     def get_for_signal_type(
#         self, signal_type: t.Type[SignalType]
#     ) -> t.Dict[str, fetch_state.TFetchedSignalMetadata]:
#         type_str = signal_type.get_name()
#         return {
#             signal_str: meta
#             for (signal_type_str, signal_str), meta in self.update_record.items()
#             if signal_type_str == type_str and meta is not None
#         }


@dataclass
class _StateTracker:
    api_cls: TSignalExchangeAPICls
    _delta: t.Optional[fetch_state.FetchDeltaTyped]
    dirty: bool = False

    @property
    def empty(self) -> bool:
        return self._delta is None

    @property
    def delta(self) -> fetch_state.FetchDeltaTyped:
        assert self._delta is not None
        return self._delta

    @delta.setter
    def delta(self, value: fetch_state.FetchDeltaTyped) -> None:
        if self._delta is None:
            old = None
            self._delta = value
        else:
            old = self._delta.updates
        self._delta.updates = self.api_cls.naive_fetch_merge(old, value.updates)
        self._delta.checkpoint = value.checkpoint
        self.dirty = True

    @property
    def checkpoint(self) -> t.Optional[fetch_state.FetchCheckpointBase]:
        return None if self._delta is None else self._delta.checkpoint


class SimpleFetchedStateStore(fetch_state.FetchedStateStoreBase):
    """
    A FetchedStateStore that does merges in memory and writes by collab
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
    ) -> t.Optional[fetch_state.FetchDeltaTyped]:
        raise NotImplementedError

    def _write_state(
        self, collab_name: str, delta: fetch_state.FetchDeltaTyped
    ) -> None:
        raise NotImplementedError

    def get_checkpoint(
        self, collab: CollaborationConfigBase
    ) -> t.Optional[fetch_state.FetchCheckpointBase]:
        return self._get_state(collab).checkpoint

    def _get_state(self, collab: CollaborationConfigBase) -> _StateTracker:
        if collab.name not in self._state:
            logging.debug("Loading state for %s", collab.name)
            delta = self._read_state(collab.name)
            self._state[collab.name] = _StateTracker(self.api_cls, delta)
        return self._state[collab.name]

    def merge(
        self,
        collab: CollaborationConfigBase,
        delta: fetch_state.FetchDeltaTyped,
    ) -> None:
        """
        Merge a FetchDeltaBase into the state.

        At the implementation's discretion, it may call flush() or the
        equivalent work.
        """

        state = self._get_state(collab)
        if len(delta.updates) == 0 and delta.checkpoint in (
            None,
            state.checkpoint,
        ):
            logging.warning("No op update for %s", collab.name)
            return
        state.delta = delta

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
            state = self._get_state(collab)
            if not state.empty:
                by_signal = state.api_cls.naive_convert_to_signal_type(
                    [signal_type], state.delta.updates
                ).get(signal_type, {})
                if by_signal:
                    ret[collab.name] = by_signal
        return ret
