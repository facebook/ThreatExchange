#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import collections
import pathlib
import time
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
            "--threat-types",
            nargs="+",
            help="Only fetch updates for indicators of the given type",
        )

    def __init__(
        self,
        start_time: int,
        stop_time: int,
        threat_types: t.List[str],
    ) -> None:
        self.start_time = start_time
        self.stop_time = stop_time
        self.threat_types = threat_types
        self.signal_types_by_name = {
            name: signal() for name, signal in meta.get_signal_types_by_name().items()
        }
        self.last_update_printed = 0
        self.counts = collections.Counter()

    def execute(self, dataset: Dataset) -> None:
        privacy_group = dataset.config.privacy_groups[0]
        self.indicator_signals = signal_base.IndicatorSignals(privacy_group)
        self.indicator_signals.load_indicators()

        # TODO: [Potential] Force full fetch if it has been 90 days since the last fetch.
        # self.start_time = (
        #     dataset.get_indicator_checkpoint()
        #     if self.start_time is None
        #     else self.start_time
        # )
        # self.stop_time = int(time.time()) if self.stop_time is None else self.stop_time
        start_time = 0
        stop_time = time.time()

        more_to_fetch = True
        next_page = None

        while more_to_fetch:
            result = TE.Net.getThreatUpdates(
                privacy_group,
                start_time=self.start_time,
                stop_time=self.stop_time,
                threat_type=self.threat_types,
                next_page=next_page,
            )
            if "data" in result:
                self._process_indicators(result["data"])
            more_to_fetch = "paging" in result and "next" in result["paging"]
            next_page = result["paging"]["next"] if more_to_fetch else None

        self.indicator_signals.store_indicators()
        for threat_type in self.counts:
            print(f"{threat_type}: {self.counts[threat_type]}")
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
                [int(app) for app in ti_json.get("applications_with_opinions")] if "applications_with_opinions" in ti_json else [],
            )

            self.indicator_signals.process_indicator(ti)
            self.counts[ti.threat_type] += 1
            self.counts["Total"] += 1

        now = time.time()
        if now - self.last_update_printed >= self.PROGRESS_PRINT_INTERVAL_SEC:
            self.last_update_printed = now
            self.stderr(f"Processed {self.counts['Total']}...")
