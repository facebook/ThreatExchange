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
    # If a client does not resume tailing the threat_updates endpoint fast enough,
    # deletion records will be removed, making it impossible to determine which
    # records should be retained without refetching the entire dataset from scratch.
    # The current implementation will retain for 90 days: TODO: Link to documentation
    DEFAULT_REFETCH_SEC = 3600 * 24 * 85  # 85 days
    MAX_CONSECUTIVE_RETRIES = 5

    @classmethod
    def init_argparse(cls, ap) -> None:
        # TODO: make continuation the default behaviour and give an option to do a full fetch
        ap.add_argument(
            "--continuation",
            action="store_true",
            help="Continue fetching updates from where you last stopped with the same threat types. This will ignore all other options given aside from --page-size.",
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
            "--types",
            nargs="+",
            help="Only fetch updates for indicators of the given type",
        )
        ap.add_argument(
            "--page-size",
            type=int,
            help="The number of updates to fetch per request, defaults to 500",
            default=500,
        )

    def __init__(
        self,
        continuation: bool,
        start_time: int,
        stop_time: int,
        types: t.List[str],
        page_size: int,
    ) -> None:
        self.continuation = continuation
        self.start_time = start_time
        self.stop_time = stop_time
        self.types = types
        self.limit = page_size
        self.last_update_printed = 0

    def execute(self, dataset: Dataset) -> None:
        request_time = int(time.time())
        for privacy_group in dataset.config.privacy_groups:
            self.counts = collections.Counter()
            self.total_count = 0
            self.deleted_count = 0
            self.indicator_store = dataset.get_indicator_store(privacy_group)
            dataset.load_indicator_cache(self.indicator_store)
            self.stop_time = request_time if self.stop_time is None else self.stop_time
            next_page = None
            if self.continuation:
                checkpoint = dataset.get_indicator_checkpoint(privacy_group)
                self.start_time = checkpoint["last_stop_time"]
                self.stop_time = request_time
                self.types = checkpoint["types"]
                if (
                    request_time - checkpoint["last_run_time"]
                    > self.DEFAULT_REFETCH_SEC
                ):
                    print("It's been a long time since a full fetch, forcing one now.")
                    self.start_time = 0

            more_to_fetch = True
            remaining_attempts = self.MAX_CONSECUTIVE_RETRIES
            while more_to_fetch:
                try:
                    result = TE.Net.getThreatUpdates(
                        privacy_group,
                        next_page,
                        start_time=self.start_time,
                        stop_time=self.stop_time,
                        types=self.types,
                        limit=self.limit,
                    )
                    if "data" in result:
                        self._process_indicators(result["data"])
                    more_to_fetch = "paging" in result and "next" in result["paging"]
                    next_page = result["paging"]["next"] if more_to_fetch else None
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
                        print(
                            f"\n{self.MAX_CONSECUTIVE_RETRIES} consecutive errors occured, shutting down!"
                        )
                        print(
                            "Please try again with 'threatexchange -c {config} experimental-fetch --continuation'."
                        )
                        return
                remaining_attempts = self.MAX_CONSECUTIVE_RETRIES

            dataset.store_indicator_cache(self.indicator_store)
            dataset.set_indicator_checkpoint(
                privacy_group,
                self.stop_time,
                request_time,
                self.types,
            )

            # TODO: simplify this output
            print(f"\nFor privacy group {privacy_group}:")
            print("\nHere is a summary from this run:")
            for threat_type in self.counts:
                print(f"{threat_type}: {self.counts[threat_type]}")
            print(
                f"Total: {self.total_count}\n{self.deleted_count} of these were deletes."
            )
            print(f"\nThis brings your total dataset to:")
            total = 0
            for threat_type in self.indicator_store.state:
                size = len(self.indicator_store.state[threat_type])
                total += size
                print(f"{threat_type}: {size}")
            print(f"Total: {total}")
            print(
                "\nYou can run 'threatexchange -c {config} experimental-fetch --continuation' to fetch future updates."
            )

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
                [int(app) for app in ti_json.get("applications_with_opinions", [])],
            )

            self.indicator_store.process_indicator(ti)
            self.counts[ti.threat_type] += 1
            self.total_count += 1
            if ti.should_delete:
                self.deleted_count += 1

        now = time.time()
        if now - self.last_update_printed >= self.PROGRESS_PRINT_INTERVAL_SEC:
            self.last_update_printed = now
            self.stderr(f"Processed {self.total_count}...")
