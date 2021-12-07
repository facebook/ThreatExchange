#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import argparse
import collections
import concurrent.futures
import csv
import datetime
import json
import os
import pathlib
import time
import typing as t

from .. import threat_updates
from ..api import ThreatExchangeAPI
from ..content_type import meta
from ..dataset import Dataset
from ..descriptor import SimpleDescriptorRollup
from ..signal_type import signal_base
from . import command_base
from . import dataset_cmd
from .dataset.simple_serialization import CliIndicatorSerialization


class FetchCommand(command_base.Command):
    """
    Download content from ThreatExchange to disk.

    Using the CollaborationConfig, download signals that
    correspond to a single collaboration, and store them in the state
    directory.

    This endpoint uses /threat_updates to fetch content sequentially, and in
    theory can be interrupted without issues.
    """

    PROGRESS_PRINT_INTERVAL_SEC = 30

    @classmethod
    def init_argparse(cls, ap) -> None:
        ap.add_argument(
            "--full",
            action="store_true",
            help="force a refetch from the beginning of time (this is almost certainly not needed)",
        )
        ap.add_argument(
            "--skip-index-rebuild",
            action="store_true",
            help="don't rebuild indices after fetch",
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
        stop_time: t.Optional[int],
        limit: t.Optional[int],
        skip_index_rebuild: bool,
    ) -> None:
        self.full = full
        self.stop_time = stop_time
        self.limit = limit
        self.skip_index_rebuild = skip_index_rebuild

        # Progress
        self.current_pgroup = 0
        self.last_update_time = 0
        # Print first update after 5 seconds
        self.last_update_printed = time.time() - self.PROGRESS_PRINT_INTERVAL_SEC + 5
        self.processed = 0
        self.counts: t.Dict[str, int] = collections.Counter()

    def execute(self, api: ThreatExchangeAPI, dataset: Dataset) -> None:
        privacy_groups = dataset.config.privacy_groups
        stores = []
        for privacy_group in privacy_groups:
            indicator_store = threat_updates.ThreatUpdateFileStore(
                dataset.state_dir,
                privacy_group,
                api.app_id,
                serialization=CliIndicatorSerialization,
            )
            stores.append(indicator_store)
            if self.full:
                indicator_store.reset()
            else:
                indicator_store.load_checkpoint()
            if indicator_store.stale:
                indicator_store.reset()
            self.last_update_time = indicator_store.fetch_checkpoint
            if len(privacy_groups) > 1:
                self.current_pgroup = privacy_group

            self._print_progress()
            if indicator_store.fetch_checkpoint >= time.time():
                continue

            delta = indicator_store.next_delta
            if self.stop_time:
                delta.end = self.stop_time
            try:
                delta.incremental_sync_from_threatexchange(
                    api, limit=self.limit, progress_fn=self._progress
                )
            except:
                self.stderr("Exception occurred! Attempting to save...")
                # Force delta to show finished
                delta.end = delta.current
                raise
            finally:
                if delta:
                    indicator_store.apply_updates(delta)

        self.stderr(f"Processed {self.processed} updates:")

        if self.processed:
            for name, count in sorted(self.counts.items(), key=lambda i: -i[1]):
                self.stderr(f"{name}: {count:+}")

        # Rebuild CLI indices
        if not self.skip_index_rebuild:
            self.stderr("Rebuilding match indices...")
            dataset_cmd.generate_cli_indices(dataset, stores)

    def _progress(self, update: threat_updates.ThreatUpdateJSON) -> None:
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

        on_privacy_group = ""
        if self.current_pgroup:
            on_privacy_group = f"on PrivacyGroup({self.current_pgroup}) "

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
            f"{processed}Currently {on_privacy_group}at {from_time}",
        )
