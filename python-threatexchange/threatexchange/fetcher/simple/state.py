# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved


from collections import defaultdict
from dataclasses import dataclass, field
import logging
import typing as t
from threatexchange.fetcher.fetch_api import SignalExchangeAPI

from threatexchange.signal_type.signal_base import SignalType
from threatexchange.fetcher import fetch_state
from threatexchange.fetcher.collab_config import CollaborationConfigBase


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
class SimpleFetchDelta(
    fetch_state.FetchDeltaWithUpdateStream[
        fetch_state.TFetchCheckpoint, fetch_state.TFetchedSignalMetadata
    ]
):
    """
    Simple class for deltas.

    If the record is set to None, this indicates the record should be
    deleted if it exists.
    """

    updates: t.Mapping[
        t.Tuple[str, str], t.Optional[fetch_state.TFetchedSignalMetadata]
    ]
    checkpoint: fetch_state.TFetchCheckpoint
    done: bool  # powers has_more

    def record_count(self) -> int:
        return len(self.updates)

    def next_checkpoint(self) -> fetch_state.TFetchCheckpoint:
        return self.checkpoint

    def has_more(self) -> bool:
        return not self.done

    def get_as_update_dict(
        self,
    ) -> t.Mapping[t.Tuple[str, str], t.Optional[fetch_state.TFetchedSignalMetadata]]:
        return self.updates


@dataclass
class _StateTracker:
    updates_by_type: t.Dict[str, t.Dict[str, fetch_state.FetchedSignalMetadata]]
    checkpoint: t.Optional[fetch_state.FetchCheckpointBase]
    dirty: bool = False

    def merge(self, newer: fetch_state.FetchDeltaWithUpdateStream) -> None:
        updates = newer.get_as_update_dict()
        if not updates:
            return
        newer_by_type: t.DefaultDict[
            str, t.List[t.Tuple[str, t.Optional[fetch_state.FetchedSignalMetadata]]]
        ] = defaultdict(list)
        for (stype, signal_str), record in updates.items():
            newer_by_type[stype].append((signal_str, record))

        for n_type, n_updates in newer_by_type.items():
            o_updates = self.updates_by_type.setdefault(n_type, {})
            for sig_str, new_record in n_updates:
                if new_record is None:
                    o_updates.pop(sig_str, None)
                else:
                    old_record = o_updates.get(sig_str)
                    if old_record:
                        new_record = new_record.merge_metadata(old_record, new_record)
                    o_updates[sig_str] = new_record
        self.checkpoint = newer.next_checkpoint()
        self.dirty = True


class SimpleFetchedStateStore(fetch_state.FetchedStateStoreBase):
    """
    Standardizes on merging on (type, indicator), merges in memory.
    """

    def __init__(
        self,
        api_cls: t.Type[SignalExchangeAPI],
    ) -> None:
        self.api_cls = api_cls
        self._state: t.Dict[str, _StateTracker] = {}

    def _read_state(
        self,
        collab_name: str,
    ) -> t.Optional[
        t.Tuple[
            t.Dict[str, t.Dict[str, fetch_state.FetchedSignalMetadata]],
            t.Optional[fetch_state.FetchCheckpointBase],
        ]
    ]:
        raise NotImplementedError

    def _write_state(
        self,
        collab_name: str,
        updates_by_type: t.Dict[str, t.Dict[str, fetch_state.FetchedSignalMetadata]],
        checkpoint: fetch_state.FetchCheckpointBase,
    ) -> None:
        raise NotImplementedError

    def get_checkpoint(
        self, collab: CollaborationConfigBase
    ) -> t.Optional[fetch_state.FetchCheckpointBase]:
        return self._get_state(collab.name).checkpoint

    def _get_state(self, collab_name: str) -> _StateTracker:
        if collab_name not in self._state:
            logging.debug("Loading state for %s", collab_name)
            read_state = self._read_state(collab_name) or ({}, None)
            self._state[collab_name] = _StateTracker(*read_state)
        return self._state[collab_name]

    def merge(  # type: ignore[override]  # fix with generics on base
        self,
        collab: CollaborationConfigBase,
        delta: fetch_state.FetchDeltaWithUpdateStream,
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
                assert state.checkpoint
                self._write_state(collab_name, state.updates_by_type, state.checkpoint)
                state.dirty = False

    def get_for_signal_type(
        self, collabs: t.List[CollaborationConfigBase], signal_type: t.Type[SignalType]
    ) -> t.Dict[str, t.Dict[str, fetch_state.FetchedSignalMetadata]]:
        st_name = signal_type.get_name()
        ret = {}
        for collab in collabs:
            state = self._get_state(collab.name)
            ret[collab.name] = state.updates_by_type.get(st_name, {})
        return ret
