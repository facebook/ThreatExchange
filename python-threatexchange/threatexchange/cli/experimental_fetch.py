#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import argparse
import csv
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
from ..descriptor import SimpleDescriptorRollup
from ..signal_type import signal_base
from . import command_base


# TODO - Once this stabalizes, move this to a new file/directory
class ThreatUpdateJSON(t.NamedTuple):
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
    def indicator(self) -> str:
        return self.raw_json["indicator"]

    @property
    def threat_type(self) -> str:
        return self.raw_json["type"]

    @property
    def time(self) -> int:
        """The time of the update"""
        return int(self.raw_json["last_updated"])

    def as_rollup(self, app_id: int) -> SimpleDescriptorRollup:
        """As a SimpleDescriptorRollup"""
        return SimpleDescriptorRollup.from_threat_updates_json(app_id, self.raw_json)

    def as_cli_csv_row(self, app_id: int) -> t.Tuple:
        """As a simple record type for the threatexchange CLI cache"""
        return (self.indicator,) + self.as_rollup(app_id).as_row()

    @staticmethod
    def te_threat_updates_fields():
        """Which fields need to be fetched from /threat_updates"""
        return SimpleDescriptorRollup.te_threat_updates_fields()


# TODO - Move this to where ThreatUpdateJSON ends up
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
        """Has this delta fetched its entire assigned range?"""
        return self.end and self.end <= self.current

    def merge(self, delta: "ThreatUpdatesDelta") -> "ThreatUpdatesDelta":
        if not self.done or self.end != delta.start:
            raise ValueError("unchecked merge!")
        self.updates.extend(delta.updates)
        self.current = delta.current
        self.end = delta.end
        self.tries = delta.tries

    def one_fetch(self, api: ThreatExchangeAPI) -> t.Dict[str, t.Any]:
        """
        Do a single fetch from ThreatExchange and store the results.

        One fetch only, please.
        """
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
                fields=ThreatUpdateJSON.te_threat_updates_fields(),
            )
        for indicator_json in self._cursor.data:
            update = ThreatUpdateJSON(indicator_json)
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
        """Split this delta into n deltas of roughly even size"""
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
    response, so can potentially contain a lot of data.

    If a client does not resume tailing the threat_updates endpoint fast enough,
    deletion records will be removed, making it impossible to determine which
    records should be retained without refetching the entire dataset from scratch.
    The API implementation will retain for 90 days:
    https://developers.facebook.com/docs/threat-exchange/reference/apis/threat-updates/
    """

    # See docstring about tailing fast enough
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
    def state_file(self) -> pathlib.Path:
        return self.path / f"{self._privacy_group}.threat_updates{Dataset.EXTENSION}"

    def __iter__(self):
        return (ThreatUpdateJSON(v) for v in self._state.values())

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
                    "last_fetch_time": self._last_fetch_time,
                    "fetch_checkpoint": self._fetch_checkpoint,
                    "state": self._state,
                },
                f,
                indent=2,
            )

    def store_as_cli_cache(self, dataset: Dataset, app_id: int) -> None:
        row_by_type = collections.defaultdict(list)
        for threat_update in self:
            rollup = threat_update.as_rollup(app_id)
            row_by_type[threat_update.threat_type].append(
                threat_update.as_cli_csv_row(app_id)
            )
        for threat_type, rows in row_by_type.items():
            path = dataset.state_dir / f"{threat_type}{dataset.EXTENSION}"
            with path.open("w") as f:
                writer = csv.writer(f)
                writer.writerows(rows)

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
                self._state.pop(update.id, None)
            else:
                self._state[update.id] = update.raw_json
        self._fetch_checkpoint = max(self._last_fetch_checkpoint, delta.current)
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
        """
        Fetch from threat_updates to get a more up-to-date copy of the data.
        """
        if self.stale:
            self.reset()

        # TODO actually implement fancy threading logic
        # alternative - instead make the API give hints about where to start
        # fetches, which will mean that fancy threading logic will be simpler
        leader = ThreatUpdatesDelta(
            self._privacy_group, self._fetch_checkpoint, end=stop_time
        )
        probes = []

        try:
            while not leader.done:
                for raw_json in leader.one_fetch(api):
                    progress_fn(ThreatUpdateJSON(raw_json))
                    limit -= 1
                    if limit == 0:
                        return
        finally:
            self.update(leader)
        return


class ExperimentalFetchCommand(command_base.Command):
    """
    Download content from ThreatExchange to disk.

    Using the CollaborationConfig, download signals that
    correspond to a single collaboration, and store them in the state
    directory.

    This endpoint uses /threat_updates to fetch content sequentially, and in
    theory can be interrupted without issues.
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
        for privacy_group in dataset.config.privacy_groups:
            indicator_store = ThreatUpdatesIndicatorStore(
                dataset.state_dir, privacy_group
            )
            if not self.full:
                indicator_store.load()
            self.last_update_time = indicator_store.fetch_checkpoint
            self.current_pgroup = privacy_group

            self._print_progress()
            if indicator_store.fetch_checkpoint >= time.time():
                continue

            try:
                indicator_store.sync_from_threatexchange(
                    api,
                    limit=self.limit or 0,
                    stop_time=self.stop_time,
                    progress_fn=self._progress,
                )
            except:
                self.stderr("Encountered an exception! Attempting to save progress...")
                raise
            finally:
                indicator_store.store()
        if not self.processed:
            return
        self.stderr(f"Processed {self.processed} updates:")
        # Now store our signal types
        indicator_store.store_as_cli_cache(dataset, api.app_id)

        for name, count in sorted(self.counts.items(), key=lambda i: -i[1]):
            self.stderr(f"{name}: {count:+}")

    def _progress(self, update: ThreatUpdateJSON) -> None:
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

        from_time = ""
        if not self.last_update_time:
            from_time = "ages long past"
        elif self.last_update_time >= time.time():
            from_time = "moments ago"
        else:
            delta = datetime.datetime.utcfromtimestamp(
                time.time()
            ) - datetime.datetime.utcfromtimestamp(self.last_update_time)
            parts = []
            for name, div in (
                ("year", datetime.timedelta(days=365)),
                ("day", datetime.timedelta(days=1)),
                ("hour", datetime.timedelta(hours=1)),
                ("minute", datetime.timedelta(minutes=1)),
                ("second", datetime.timedelta(seconds=1)),
            ):
                val, delta = divmod(delta, div)
                if val or parts:
                    parts.append((val, name))

            from_time = "now"
            if parts:
                str_parts = []
                for val, name in parts:
                    if str_parts:
                        str_parts.append(f"{val:02}{name[0]}")
                    else:
                        s = "s" if val > 1 else ""
                        str_parts.append(f"{val} {name}{s} ")
                from_time = f"{''.join(str_parts).strip()} ago"

        self.stderr(
            f"{processed}Currently on PrivacyGroup({self.current_pgroup}),",
            f"from {from_time}",
        )
