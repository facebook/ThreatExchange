# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Helpers and wrappers around the /threat_updates endpoint.
"""

import json
import os
import pathlib
import time
import typing as t
from dataclasses import dataclass

from .api import ThreatExchangeAPI, _CursoredResponse
from .descriptor import SimpleDescriptorRollup


class ThreatUpdateSerialization:
    """
    A wrapper for converting records fetched from /threat_updates
    """

    @property
    def key(self):
        """This should either be the indicator type+string or id"""
        raise NotImplementedError

    @classmethod
    def from_threat_updates_json(cls, app_id: int, te_json):
        raise NotImplementedError

    @classmethod
    def te_threat_updates_fields(cls):
        """Which &fields= arguments need to be passed for this serialization"""
        raise NotImplementedError


@dataclass
class ThreatUpdateJSON(ThreatUpdateSerialization):
    """A thin wrapper around the /threat_updates API return"""

    raw_json: t.Dict[str, t.Any]

    @property
    def should_delete(self) -> bool:
        """This record is a tombstone, and we should delete our copy"""
        # This should just be should_delete only, but see
        # https://github.com/facebook/ThreatExchange/issues/834
        return self.raw_json["should_delete"] or "descriptors" not in self.raw_json

    @property
    def key(self):
        return self.id

    @property
    def id(self) -> int:
        return int(self.raw_json["id"])

    @property
    def indicator(self) -> str:
        return self.raw_json["indicator"]

    @property
    def threat_type(self) -> str:
        return self.raw_json["type"]

    @property
    def time(self) -> int:
        """The time of the update"""
        return int(self.raw_json["last_updated"])

    @classmethod
    def from_threat_updates_json(cls, app_id, te_json):
        return cls(te_json)

    @classmethod
    def te_threat_updates_fields(cls) -> t.Tuple[str, ...]:
        # Could also return empty here, but this set is useful for basically
        # any serialization, and so it makes sense to fetch it for future processing
        # (even though it's verbose)
        return SimpleDescriptorRollup.te_threat_updates_fields()


class ThreatUpdatesDelta:
    """
    A class for tracking a raw stream of /threat_updates

    Any integration with ThreatExchange involves the creation of a local copy
    of the data. /threat_updates sends changes to that data in either the form
    of an insert/update or a delete.

    A delta is a stream of updates and deletes, which when applied to an
    existing database will give you the current set of live records.

    As a parallelization trick, if you need to fetch between t1 and t3,
    you can pick a point between them, t2, and fetch [t1, t2) and [t2, t3)
    simulatenously, and the merging of the two is guaranteed to be the same
    as [t1, t3). The split() and merge() commands aid with this operation
    """

    def __init__(
        self,
        privacy_group: int,
        start: int = 0,
        end: t.Optional[int] = None,
        types: t.Iterable[str] = (),
    ) -> None:
        self.privacy_group = privacy_group
        self.updates: t.List = []
        self.current = start
        self.start = start
        self.end = end
        self.types = list(types)

        self._cursor: t.Optional[_CursoredResponse] = None

    @property
    def done(self) -> bool:
        """Has this delta fetched its entire assigned range?"""
        return bool(self.end and self.end <= self.current)

    def __bool__(self):
        return self.done or bool(self.updates)

    def __iter__(self):
        return iter(self.updates)

    def merge(self, delta: "ThreatUpdatesDelta") -> None:
        """
        Merge the earlier delta (this object) with a later delta.

        If you have
        t1 ---> t2 ---> t3
        t1.merge(t2).merge(t3) is valid, and will give you a range from t1-t3
        """
        if not self.done or self.end != delta.start:
            raise ValueError("unchecked merge!")
        self.updates.extend(delta.updates)
        self.current = delta.current
        self.end = delta.end

    def one_fetch(self, api: ThreatExchangeAPI):
        """
        Do a single fetch from ThreatExchange and store the results.

        One fetch only, please.
        """
        if self.done:
            return
        now = time.time()
        if not self._cursor:
            self._cursor = api.get_threat_updates(
                self.privacy_group,
                page_size=500,
                start_time=self.start,
                stop_time=self.end,
                types=self.types,
                fields=ThreatUpdateJSON.te_threat_updates_fields(),
                decode_fn=ThreatUpdateJSON,
            )
        for update in self._cursor.next():
            self.updates.append(ThreatUpdateJSON(update.raw_json))
            # Is supposed to be strictly increasing
            self.current = max(update.time, self.current)
        if self._cursor.done:
            if not self.end:
                self.end = int(now)
            self.current = self.end

        return self._cursor.data

    def split(
        self, n: int
    ) -> t.Tuple["ThreatUpdatesDelta", t.List["ThreatUpdatesDelta"]]:
        """Split this delta into n deltas of roughly even size"""
        tar = self.end or time.time()
        diff = int((tar - self.current) // (n + 1))
        if diff <= 0:
            return self, []
        end = self.end
        prev = self
        new_deltas = []
        for i in range(n - 1):
            new_start = prev.start + diff
            new_deltas.append(
                ThreatUpdatesDelta(
                    self.privacy_group,
                    new_start,
                )
            )
        prev.end = end

        return self, new_deltas

    def incremental_sync_from_threatexchange(
        self,
        api: ThreatExchangeAPI,
        *,
        limit: t.Optional[int] = None,
        progress_fn=lambda x: None,
    ) -> None:
        """
        Fetch from threat_updates to get a more up-to-date copy of the data.
        """

        # TODO actually implement fancy threading logic
        # alternative - instead make the API give hints about where to start
        # fetches, which will mean that fancy threading logic will be simpler
        while not self.done:
            for update in self.one_fetch(api):
                progress_fn(update)
                if limit is not None:
                    limit -= 1
                    if limit <= 0:
                        return


class ThreatUpdateCheckpoint(t.NamedTuple):
    """
    State about the progress of a /threat_updates-backed state.

    If a client does not resume tailing the threat_updates endpoint fast enough,
    deletion records will be removed, making it impossible to determine which
    records should be retained without refetching the entire dataset from scratch.
    The API implementation will retain for 90 days:
    https://developers.facebook.com/docs/threat-exchange/reference/apis/threat-updates/
    """

    # See docstring about tailing fast enough
    DEFAULT_REFETCH_SEC: int = 3600 * 24 * 85  # 85 days

    # When was the last time we started or the furthest we've seen,
    # to check against the store getting too stale
    last_fetch_time: int = 0
    # Where should we resume from?
    fetch_checkpoint: int = 0

    def get_updated(self, delta: ThreatUpdatesDelta) -> "ThreatUpdateCheckpoint":
        # If starting from 0, this is the first fetch, in which case the first update
        # means that we fetched now.
        last_fetch_time = self.last_fetch_time
        if last_fetch_time == 0:
            last_fetch_time = int(time.time())

        return ThreatUpdateCheckpoint(
            last_fetch_time=max(last_fetch_time, delta.current),
            fetch_checkpoint=max(self.fetch_checkpoint, delta.current),
        )

    @property
    def stale(self):
        """Is this checkpoint so old as to be invalid?"""
        return self.last_fetch_time + self.DEFAULT_REFETCH_SEC < time.time()


class ThreatUpdatesStore:
    """
    A wrapper for ThreatIndicator records for a single Collaboration

    There is a unique file for each combination of:
     * IndicatorType
     * PrivacyGroup

    The contents of file does not strip anything from the API
    response, so can potentially contain a lot of data.
    """

    def __init__(
        self,
        privacy_group: int,
    ) -> None:
        self.privacy_group = privacy_group
        self.checkpoint: t.Optional[ThreatUpdateCheckpoint] = None

    @property
    def fetch_checkpoint(self):
        return self.checkpoint.fetch_checkpoint

    def reset(self) -> None:
        """Toss old state and begin anew"""
        self.checkpoint = ThreatUpdateCheckpoint()

    @property
    def next_delta(self) -> ThreatUpdatesDelta:
        """Return the next delta that should be applied"""
        return ThreatUpdatesDelta(
            self.privacy_group,
            self.checkpoint.fetch_checkpoint if self.checkpoint else 0,
            None,
        )

    def load_checkpoint(self) -> None:
        self.checkpoint = self._load_checkpoint()

    def _load_checkpoint(self) -> ThreatUpdateCheckpoint:
        """Load the state of the threat_updates checkpoints"""
        raise NotImplementedError

    def _store_checkpoint(self, checkpoint: ThreatUpdateCheckpoint) -> None:
        """Save the state of the threat_updates checkpoints after a succesful apply"""
        raise NotImplementedError

    def _apply_updates_impl(
        self,
        delta: ThreatUpdatesDelta,
        post_apply_fn=lambda x: None,
    ) -> None:
        """Apply delta to state and store it"""
        raise NotImplementedError

    @property
    def stale(self) -> bool:
        """Is this state so old that it might be invalid?"""
        return self.checkpoint.stale if self.checkpoint else False

    def apply_updates(
        self,
        delta: ThreatUpdatesDelta,
        post_apply_fn=lambda x: None,
    ) -> None:
        """Merge updates to the data store"""
        if delta.start != 0:
            assert (
                self.checkpoint and delta.start <= self.checkpoint.fetch_checkpoint
            ), "gap in delta record"
            assert not self.stale, "attempted to apply stale delta"

        # It's possible the fetch completed but has no records
        if delta.updates:
            self._apply_updates_impl(delta, post_apply_fn)
        if self.checkpoint:
            self.checkpoint = self.checkpoint.get_updated(delta)
            self._store_checkpoint(self.checkpoint)


class ThreatUpdateFileStore(ThreatUpdatesStore):
    """
    A simple file storage (in lieu of DB) with in-memory merge
    """

    def __init__(
        self,
        state_dir: pathlib.Path,
        privacy_group: int,
        app_id: int,
        *,
        serialization=ThreatUpdateJSON,
    ) -> None:
        super().__init__(privacy_group)
        self.path = state_dir
        self.app_id = app_id
        self._serialization = serialization
        self._cached_state: t.Optional[t.Dict[str, t.Any]] = None

    @property
    def checkpoint_file(self) -> pathlib.Path:
        return self.path / f"{self.privacy_group}.threat_updates.checkpoint"

    def reset(self):
        super().reset()
        if self._cached_state:
            self._cached_state.clear()

    def _load_checkpoint(self) -> ThreatUpdateCheckpoint:
        """Load the state of the threat_updates checkpoints from state directory"""
        if not self.checkpoint_file.exists():
            return ThreatUpdateCheckpoint()

        with self.checkpoint_file.open("r") as f:
            checkpoint_json = json.load(f)
            return ThreatUpdateCheckpoint(
                checkpoint_json["last_fetch_time"],
                checkpoint_json["fetch_checkpoint"],
            )

    def _store_checkpoint(self, checkpoint: ThreatUpdateCheckpoint) -> None:
        with self.checkpoint_file.open("w") as f:
            json.dump(
                {
                    "last_fetch_time": checkpoint.last_fetch_time,
                    "fetch_checkpoint": checkpoint.fetch_checkpoint,
                },
                f,
                indent=2,
            )

    def load_state(self, allow_cached=True):
        if not self.path.exists():
            return {}
        if not allow_cached or self._cached_state is None:
            self._cached_state = {
                item.key: item for item in self._serialization.load(self.path)
            }
        return self._cached_state

    def _apply_updates_impl(
        self, delta: ThreatUpdatesDelta, post_apply_fn=lambda x: None
    ) -> None:
        os.makedirs(self.path, exist_ok=True)
        state = {}
        if delta.start > 0:
            state = self.load_state()
        for update in delta:
            item = self._serialization.from_threat_updates_json(
                self.app_id, update.raw_json
            )
            if update.should_delete:
                state.pop(item.key, None)
            else:
                state[item.key] = item

        self._cached_state = state
        self._serialization.store(self.path, state.values())
