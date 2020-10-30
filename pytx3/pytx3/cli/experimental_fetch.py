#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import collections
import pathlib
import time
import typing as t
from .. import TE
from ..dataset import Dataset
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

    @classmethod
    def init_argparse(cls, ap) -> None:
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
            "--owner",
            type=int,
            help="Only fetch updates for indicators that the given app has a descriptor for",
        )
        ap.add_argument(
            "--threat-types",
            nargs="+",
            help="Only fetch updates for indicators of the given type",
        )
        ap.add_argument(
            "--additional-tags",
            nargs="+",
            help="Only fetch updates for indicators that have a descriptor with each of these tags",
        )

    def __init__(
        self,
        start_time: int,
        stop_time: int,
        owner: int,
        threat_types: t.List[str],
        additional_tags: t.List[str],
    ) -> None:
        self.start_time = start_time
        self.stop_time = stop_time
        self.owner = owner
        self.threat_types = threat_types
        self.additional_tags = additional_tags
        self.signal_types_by_name = {
            name: signal() for name, signal in meta.get_signal_types_by_name().items()
        }
        self.last_update_printed = 0
        self.counts = collections.Counter()

    def execute(self, dataset: Dataset) -> None:
        # TODO: [Potential] Force full fetch if it has been 90 days since the last fetch.
        self.start_time = (
            dataset.get_indicator_checkpoint()
            if self.start_time is None
            else self.start_time
        )
        self.stop_time = int(time.time()) if self.stop_time is None else self.stop_time
        dataset.load_indicator_cache(self.signal_types_by_name.values())
        more_to_fetch = True
        next_page = None

        while more_to_fetch:
            result = TE.Net.getThreatUpdates(
                dataset.config.privacy_groups[0],
                start_time=self.start_time,
                stop_time=self.stop_time,
                owner=self.owner,
                threat_type=self.threat_types,
                additional_tags=self.additional_tags,
                next_page=next_page,
            )
            if "data" in result:
                self._process_indicators(result["data"])
            more_to_fetch = "paging" in result and "next" in result["paging"]
            next_page = result["paging"]["next"] if more_to_fetch else None

        for signal_name, signal_type in self.signal_types_by_name.items():
            if signal_name not in self.counts:
                continue
            dataset.store_indicator_cache(signal_type)
            print(f"{signal_name}: {self.counts[signal_name]}")

        dataset.record_indicator_checkpoint(self.stop_time)

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
                int(ti_json.get("last_updated")),
                ti_json.get("status"),
                ti_json.get("is_expired"),
                ti_json.get("tags"),
                [int(app) for app in ti_json.get("applications_with_opinions")],
                int(ti_json.get("expire_time")) if "expire_time" in ti_json else None,
            )

            match = False
            for signal_name, signal_type in self.signal_types_by_name.items():
                if signal_type.process_indicator(ti):
                    match = True
                    self.counts[signal_name] += 1
            if match:
                self.counts["all"] += 1

        now = time.time()
        if now - self.last_update_printed >= self.PROGRESS_PRINT_INTERVAL_SEC:
            self.last_update_printed = now
            self.stderr(f"Processed {self.counts['all']}...")
