#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import collections
import pathlib
import time
import urllib
import typing as t
from .. import TE
from ..dataset import Dataset
from ..signal_type import signal_base
from ..indicator import ThreatIndicator
from ..content_type import meta
from . import command_base


class ExperimentalFetchCommand(command_base.Command):
    """
    WARNING: This is experimental, you probably want to use "Fetch" instead.

    Download content from ThreatExchange to disk.

    Using the CollaborationConfig, identify ThreatPrivacyGroup that
    corresponds to a single collaboration and fetch related threat updates.
    """

    PROGRESS_PRINT_INTERVAL_SEC = 30
    DEFAULT_REFETCH_SEC = 3600 * 24 * 85  # 85 days

    @classmethod
    def init_argparse(cls, ap) -> None:
        ap.add_argument(
            "--continuation",
            action="store_true",
            help="Fetch updates that you are missing, this overrides all other given values (i.e. start-time)",
        )
        ap.add_argument(
            "--start-time",
            type=int,
            help="Fetch updates that occured on or after this timestamp",
        )
        ap.add_argument(
            "--stop-time",
            type=int,
            help="Fetch updates that occured before this timestamp",
        )
        ap.add_argument(
            "--threat-types",
            nargs="+",
            help="Only fetch updates for indicators of the given type",
        )
        ap.add_argument(
            "--page-size",
            type=int,
            help="The number of updates to fetch per request, defaults to 100",
            default=100,
        )

    def __init__(
        self,
        continuation: bool,
        start_time: int,
        stop_time: int,
        threat_types: t.List[str],
        page_size: int,
    ) -> None:
        self.continuation = continuation
        self.start_time = start_time
        self.stop_time = stop_time
        self.threat_types = threat_types
        self.limit = page_size
        self.last_update_printed = 0
        self.counts = collections.Counter()
        self.total_count = 0
        self.deleted_count = 0

    def execute(self, dataset: Dataset) -> None:
        request_time = int(time.time())
        privacy_group = dataset.config.privacy_groups[0]
        self.indicator_signals = signal_base.IndicatorSignals(privacy_group)
        dataset.load_indicator_cache(self.indicator_signals)
        self.stop_time = request_time if self.stop_time is None else self.stop_time
        next_page = None
        if self.continuation:
            checkpoint = dataset.get_indicator_checkpoint(privacy_group)
            self.start_time = checkpoint["last_stop_time"]
            self.stop_time = request_time
            self.threat_types = checkpoint["threat_types"]
            next_page = checkpoint["url"]
            if request_time - checkpoint["last_run_time"] > self.DEFAULT_REFETCH_SEC:
                print("It's been a long time since a full fetch, forcing one now.")
                self.start_time = 0

        more_to_fetch = True
        remaining_attempts = 5

        while more_to_fetch:
            try:
                result = TE.Net.getThreatUpdates(
                    privacy_group,
                    start_time=self.start_time,
                    stop_time=self.stop_time,
                    threat_type=self.threat_types,
                    next_page=next_page,
                    limit=self.limit,
                )
                if "data" in result:
                    self._process_indicators(result["data"])
                more_to_fetch = "paging" in result and "next" in result["paging"]
                next_page = result["paging"]["next"] if more_to_fetch else ""
            except Exception as e:
                remaining_attempts -= 1
                print(f"The following error occured:\n{e}")
                if type(e) is urllib.error.HTTPError:
                    print(e.read())
                if remaining_attempts > 0:
                    print(f"\nTrying again {remaining_attempts} more times.")
                    time.sleep(5)
                    continue
                else:
                    print("\n5 consecutive errors occured, saving state and shutting down!")
                    break
            remaining_attempts = 5

        dataset.store_indicator_cache(self.indicator_signals)
        dataset.record_indicator_checkpoint(
            privacy_group, self.stop_time, request_time, self.threat_types, next_page
        )
        print("\nHere is a summary from this run:")
        for threat_type in self.counts:
            print(f"{threat_type}: {self.counts[threat_type]}")
        print(f"Total: {self.total_count}")
        print(f"{self.deleted_count} of these were deletes.")
        print("\nYou can run 'threatexchange -c {config} experimental-fetch --continuation' to continue from the last successful point.")
        return

    def _process_indicators(
        self,
        indicators: list,
    ) -> None:
        """Process indicators"""
        for ti_json in indicators:
            ti = ThreatIndicator(
                int(ti_json.get("id")),
                ti_json.get("indicator"),
                ti_json.get("type"),
                int(ti_json.get("creation_time")),
                int(ti_json.get("last_updated")) if "last_updated" in ti_json else None,
                ti_json.get("status"),
                ti_json.get("should_delete"),
                ti_json.get("tags") if "tags" in ti_json else [],
                [int(app) for app in ti_json.get("applications_with_opinions")]
                if "applications_with_opinions" in ti_json
                else [],
            )

            self.indicator_signals.process_indicator(ti)
            self.counts[ti.threat_type] += 1
            self.total_count += 1
            if ti.should_delete:
                self.deleted_count += 1

        now = time.time()
        if now - self.last_update_printed >= self.PROGRESS_PRINT_INTERVAL_SEC:
            self.last_update_printed = now
            self.stderr(f"Processed {self.total_count}...")
