#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import argparse
import collections
import concurrent.futures
import datetime
import json
import os
import pathlib
import time
import typing as t

from ..api import ThreatExchangeAPI
from ..dataset import Dataset
from ..descriptor import ThreatDescriptor, SimpleDescriptorRollup
from ..indicator import ThreatIndicator
from ..signal_type import signal_base
from . import command_base


class ThreatUpdate(t.NamedTuple):
    """A thin wrapper around the /threat_updates API return"""

    raw_json: t.Dict[str, t.Any]

    @property
    def should_delete(self) -> bool:
        """This record is a tombstone, and we should delete our copy"""
        return self.raw_json["should_delete"]

    @property
    def id(self) -> int:
        return int(self.raw_json["id"])

    @property
    def threat_type(self) -> str:
        return self.raw_json["type"]

    @property
    def time(self) -> int:
        return int(self.raw_json["last_updated"])

    @staticmethod
    def te_threat_updates_fields():
        return SimpleDescriptorRollup.te_threat_updates_fields()


class ThreatUpdatesDelta:
    def __init__(
        self, privacy_group: int, start: int = 0, end: t.Optional[int] = None
    ) -> None:
        self.privacy_group = privacy_group
        self.updates = []
        self.current = start
        self.start = start
        self.end = end

        self._cursor = None

    @property
    def done(self) -> bool:
        return self.end and self.end <= self.current

    def merge(self, delta: "ThreatUpdatesDelta") -> "ThreatUpdatesDelta":
        if not self.done or self.end != delta.start:
            raise ValueError("unchecked merge!")
        self.updates.extend(delta.updates)
        self.current = delta.current
        self.end = delta.end
        self.tries = delta.tries

    def one_fetch(self, api: ThreatExchangeAPI) -> t.Dict[str, t.Any]:
        """One fetch only, please"""
        if self.done:
            return
        now = time.time()
        if self._cursor:
            self._cursor.next()
        else:
            self._cursor = api.get_threat_updates(
                self.privacy_group,
                page_size=500,
                start_time=self.start,
                stop_time=self.end,
                fields=ThreatUpdate.te_threat_updates_fields(),
            )
        for indidicator_json in self._cursor.data:
            update = ThreatUpdate(indidicator_json)
            self.updates.append(update)
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
        tar = self.end or time.time()
        diff = (tar - self.current_time) // (n + 1)
        if diff <= 0:
            return self, []
        end = self.end
        prev = self
        new_deltas = []
        for i in range(n - 1):
            prev.end = prev.start + diff
            new_deltas.append(ThreatUpdatesDelta(self.privacy_group, prev.end))
        prev.end = end

        return self, new_deltas


class ThreatUpdatesIndicatorStore:
    """
    A wrapper for ThreatIndicator records for a single Collaboration

    There is a unique file for each combination of:
     * IndicatorType
     * PrivacyGroup

    The contents of file does not strip anything from the API
    response, so can potentially contain a lot of data
    """

    # If a client does not resume tailing the threat_updates endpoint fast enough,
    # deletion records will be removed, making it impossible to determine which
    # records should be retained without refetching the entire dataset from scratch.
    # The current implementation will retain for 90 days: TODO: Link to documentation
    DEFAULT_REFETCH_SEC = 3600 * 24 * 85  # 85 days

    def __init__(self, state_dir: pathlib.Path, privacy_group: int) -> None:
        self.path = state_dir
        self._privacy_group = privacy_group
        # Resettable
        self._state: t.Dict[int, t.Any] = {}
        self._last_fetch_time = 0
        self._fetch_checkpoint = 0

    def reset(self) -> None:
        self._state.clear()
        self._last_fetch_time = 0
        self._last_fetch_checkpoint = 0

    @property
    def state_file() -> pathlib.Path:
        return self.path / f"{self._privacy_group}.threat_updates{Dataset.EXTENSION}"

    def load(self) -> None:
        """Load the state of the threat_updates checkpoints from state directory"""
        self.reset()

        # No state directory = no state
        state_path = self.state_file
        if not state_path.exists():
            return
        with state_path.open("r") as s:
            raw_json = json.load(s)
            self._state = raw_json["state"]
            self._last_fetch_time = raw_json["last_fetch_time"]
            self._fetch_checkpoint = raw_json["fetch_checkpoint"]

    def store(self) -> None:
        os.makedirs(self.path, exist_ok=True)
        with self.state_file.open("w") as f:
            json.dump(
                {
                    "state": self._state,
                    "last_fetch_time": self._last_fetch_time,
                    "fetch_checkpoint": self._fetch_checkpoint,
                },
                f,
                indent=2,
            )

    @property
    def stale(self) -> bool:
        """Is this state so old that it might be invalid?"""
        return self._last_fetch_time + self.DEFAULT_REFETCH_SEC < time.time()

    @property
    def fetch_checkpoint(self) -> int:
        return self._fetch_checkpoint

    def update(self, delta: ThreatUpdatesDelta) -> None:
        for update in delta.updates:
            if update.should_delete:
                state.pop(update.id, None)
            else:
                state[update.id] = update.raw_json
        self._last_fetch_checkpoint = max(self._last_fetch_checkpoint, delta.current)
        self._last_fetch_time = max(self._last_fetch_time, delta.current)

    def sync_from_threatexchange(
        self,
        api: ThreatExchangeAPI,
        *,
        limit: int = 0,
        stop_time: t.Optional[int] = None,
        threads: int = 1,
        progress_fn=None,
    ) -> None:
        if self.stale:
            self.reset()

        leader = ThreatUpdatesDelta(
            self._privacy_group, self._fetch_checkpoint, end=stop_time
        )
        probes = []

        while not leader.done:
            for raw_json in leader.one_fetch(api):
                progress_fn(ThreatUpdate(raw_json))
                limit -= 1
                if limit == 0:
                    return
        return


class ExperimentalFetchCommand(command_base.Command):
    """
    WARNING: This is experimental, you probably want to use "fetch" instead.

    Download content from ThreatExchange to disk.

    Using the CollaborationConfig, download signals that
    correspond to a single collaboration, and store them in the state
    directory.
    """

    PROGRESS_PRINT_INTERVAL_SEC = 1

    @classmethod
    def init_argparse(cls, ap) -> None:
        ap.add_argument(
            "--full",
            action="store_true",
            help="force a refetch from the beginning of time (this is almost certainly not needed)",
        )
        ap.add_argument("--limit", type=int, help="stop after fetching this many items")
        ap.add_argument(
            "--stop-time",
            type=int,
            help="only fetch until this point",
        )

    def __init__(
        self,
        full: bool,
        stop_time: int,
        limit: int,
    ) -> None:
        self.full = full
        self.stop_time = stop_time
        self.limit = limit

        # Progress
        self.current_pgroup = 0
        self.last_update_time = 0
        # Print first update after 5 seconds
        self.last_update_printed = time.time() - self.PROGRESS_PRINT_INTERVAL_SEC + 5
        self.processed = 0
        self.counts = collections.Counter()

    def execute(self, api: ThreatExchangeAPI, dataset: Dataset) -> None:
        request_time = int(time.time())

        for privacy_group in dataset.config.privacy_groups:
            indicator_store = ThreatUpdatesIndicatorStore(
                dataset.state_dir, privacy_group
            )
            if not self.full:
                indicator_store.load()

            self.last_update_time = indicator_store.fetch_checkpoint
            self.current_pgroup = privacy_group

            self._print_progress()

            indicator_store.sync_from_threatexchange(
                api,
                limit=self.limit or 0,
                stop_time=self.stop_time,
                progress_fn=self._progress,
            )
            # indicator_store.store()
        if self.processed:
            print(f"Processed {self.processed} updates:")
            for name, count in sorted(self.counts.items(), key=lambda i: -i[1]):
                print(f"{name}: {count:+}")

    def _progress(self, update: ThreatUpdate) -> None:
        self.processed += 1

        self.counts[update.threat_type] += -1 if update.should_delete else 1
        self.last_update_time = update.time

        now = time.time()
        if now - self.last_update_printed >= self.PROGRESS_PRINT_INTERVAL_SEC:
            self.last_update_printed = now
            self._print_progress()

    def _print_progress(self):
        processed = ""
        if self.processed:
            processed = f"Downloaded {self.processed} updates. "

        from_time = "ages long past"
        if self.last_update_time:

            delta = datetime.datetime.now() - datetime.datetime.utcfromtimestamp(
                self.last_update_time
            )
            parts = []
            for name, div in (
                ("Y", datetime.timedelta(days=365)),
                ("M", datetime.timedelta(days=30)),
                ("d", datetime.timedelta(days=1)),
                ("h", datetime.timedelta(hours=1)),
                ("m", datetime.timedelta(minutes=1)),
                ("s", datetime.timedelta(seconds=1)),
            ):
                val, delta = divmod(
                    delta,
                    div
                )
                if val:
                    parts.append((val, name))
                    # if len(parts) == 2:
                    #     break

            from_time = "now"
            if parts:
                str_parts =  []
                for val, name in parts:
                    # s = "s" if val > 1 else ""
                    str_parts.append(f"{val}{name}")
                from_time = f"{' '.join(str_parts)} ago"

        self.stderr(
            f"{processed}Currently on PrivacyGroup({self.current_pgroup}),",
            f"from {from_time}",
        )
