#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
A command to fetch datasets from ThreatExchange based on the collab config
"""

import argparse
import collections
import concurrent.futures
import datetime
import inspect
import pathlib
import time
import typing as t
import urllib.parse

from ..api import ThreatExchangeAPI
from ..collab_config import CollaborationConfig
from ..content_type import meta
from ..dataset import Dataset, FetchCheckpoint
from ..descriptor import ThreatDescriptor
from ..signal_type import signal_base
from . import command_base


class FetchType:
    """Typed helper determine_fetch_type."""

    def __init__(self, from_timestamp: float) -> None:
        self.from_timestamp = from_timestamp

    @property
    def is_full(self) -> bool:
        return not self.from_timestamp

    @property
    def is_incremental(self) -> bool:
        return not self.is_full

    @classmethod
    def Full(cls) -> "FetchType":
        return cls(0.0)

    @classmethod
    def Incremental(cls, from_timestamp: float) -> "FetchType":
        return cls(from_timestamp)


class TagFetchCommand(command_base.Command):
    """
    Download content from ThreatExchange to disk.

    Using the CollaborationConfig, identify ThreatDescriptors that
    correspond to a single collaboration, and store them in the state
    directory.

    You can then use the match command to search against this directory for
    the simple content, or you can use the produced files (which by default
    live in your home directory with a name based on the collaboration, but
    can be overridden with the --state-dir argument) to load into your own
    infrastructure to more efficiently match against the downloaded hashes.

    The exact format of each file is determined by the implementation of the
    signal types, but or usually optimized for easy re-use, such as .csv or
    .tsv.
    """

    # Enforced by the endpoint
    MAX_DESCRIPTOR_FETCH_SIZE = 20
    DEFAULT_REFETCH_SEC = 3600 * 24 * 7  # 1 week
    UP_TO_DATE_SEC = 60  # 1 minute
    PROGRESS_PRINT_INTERVAL_SEC = 30

    @classmethod
    def init_argparse(cls, ap) -> None:
        ap.add_argument(
            "--sample",
            action="store_true",
            help="Only fetch a sample of data instead of the whole dataset",
        )
        ap.add_argument(
            "--clear",
            action="store_true",
            help="Don't fetch anything, just clear the dataset",
        )
        ap.add_argument(
            "--full", action="store_true", help="Force a full refresh of data."
        )
        ap.add_argument(
            "--until-timestamp",
            type=int,
            default=0,
            help=(
                "Instead of fetching all the data, "
                "incrementally fetch up to this time"
            ),
        )
        ap.add_argument(
            "--only-signals",
            "-o",
            nargs="+",
            metavar="signal",
            choices=sorted(meta.get_signal_types_by_name()),
            help="Only download the specified signal types.",
        )
        ap.add_argument(
            "--not-signals",
            "-n",
            nargs="+",
            metavar="signal",
            choices=sorted(meta.get_signal_types_by_name()),
            help="Don't fetch the specified signal types.",
        )

    def __init__(
        self,
        sample: bool,
        clear: bool = False,
        until_timestamp: int = 0,
        full: bool = False,
        only_signals: t.Collection[str] = (),
        not_signals: t.Collection[str] = (),
    ) -> None:
        """Has default arguments because it's called by match command"""
        self.sample = sample
        self.clear = clear

        now = time.time()
        self.until_timestamp = min(float(until_timestamp or now), now)
        self.force_full = full
        self.force_incremental = bool(until_timestamp) and not full
        # Cause first print to be after ~5 seconds
        self.last_update_printed = now - self.PROGRESS_PRINT_INTERVAL_SEC + 5

        if only_signals or not_signals:
            # TODO - this is fixable by storing checkpoints per signal type
            self.stderr(
                "Ignoring some signal types will lead to only part of",
                "the dataset being fetched until fixed with --full.",
            )

        only_signals = only_signals or meta.get_signal_types_by_name()
        not_signals = not_signals or ()
        self.signal_types_by_name = {
            name: signal()
            for name, signal in meta.get_signal_types_by_name().items()
            if name in only_signals and name not in not_signals
        }

    def determine_fetch_type(self, checkpoint: FetchCheckpoint) -> FetchType:
        """Based on the checkpoint and options, determine what fetch we are doing"""
        if self.force_full or self.sample:
            return FetchType.Full()

        fetch_from_timestamp = checkpoint.last_fetch

        if not checkpoint.last_fetch:
            return FetchType.Full()

        if (
            not self.force_incremental
            and time.time() - checkpoint.last_full_fetch > self.DEFAULT_REFETCH_SEC
        ):
            self.stderr("It's been a long time since a full fetch, forcing one now.")
            return FetchType.Full()

        return FetchType.Incremental(checkpoint.last_fetch)

    def execute(self, api: ThreatExchangeAPI, dataset: Dataset) -> None:
        if self.clear:
            dataset.clear_cache()
            return

        fetch_type = self.determine_fetch_type(dataset.get_fetch_checkpoint())

        if fetch_type.is_incremental:
            if fetch_type.from_timestamp >= self.until_timestamp:
                self.stderr("Already up-to-date.")
                return
            start_time_str = datetime.datetime.utcfromtimestamp(
                int(fetch_type.from_timestamp)
            ).strftime("%Y-%m-%d %H:%M:%S")
            self.stderr(
                f"Doing an incremental update from {start_time_str}. ",
                (
                    "This will miss some updates and deletes of previously fetched data, "
                    "use --full to force a refetch."
                ),
                sep="\n",
            )
            # Note that merging into this is error prone - tagging and untagging a descriptor
            # can move its position in the fetch, leading to the following
            # 1. Descriptor1 (D1) => Tag1 (T1)
            # 2. Fetch stores D1: T1
            # 3. D1 untagged, re-tagged with T2
            # 4. fetch load D1: T1
            # 5. fetch finds D1: T2
            # 6. Naive merge yield D1: T1, T2
            #
            # We're relying on full fetching to fix this eventually (as well as deletes)
            dataset.load_cache(self.signal_types_by_name.values())

        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as id_fetch_pool:

            seen_td_ids = set()

            counts: t.Dict[str, int] = collections.Counter()
            errors: t.Dict[str, int] = collections.Counter()

            tags_to_fetch = (
                list(dataset.config.labels.keys()) if dataset.config.labels else []
            )
            only_first_fetch = False

            if self.sample:
                if dataset.config.sample_tag:
                    tags_to_fetch = [dataset.config.sample_tag]
                else:
                    only_first_fetch = True

            # TODO - Write a checkpoint file on descriptors, potentially resume from that file
            #        if we exit

            def consume_descriptors(dq: collections.deque) -> int:
                """Process descriptors in order"""
                item = dq.popleft()
                # TODO - consider a timeout
                descriptors = item.result()
                for descriptor in descriptors:
                    any_match = False
                    for signal_name, signal_type in self.signal_types_by_name.items():
                        is_match = False
                        try:
                            is_match = signal_type.process_descriptor(descriptor)
                        except Exception:
                            errors[signal_name] += 1
                        if is_match:
                            any_match = True
                            counts[signal_name] += 1
                    if any_match:
                        counts["all"] += 1
                now = time.time()
                if now - self.last_update_printed >= self.PROGRESS_PRINT_INTERVAL_SEC:
                    self.last_update_printed = now
                    self.stderr(f"Processed {counts['all']}...")
                return len(descriptors)

            for tag_name in tags_to_fetch:
                tag_id = api.get_tag_id(tag_name)
                if not tag_id:
                    continue
                pending_futures: t.Deque[
                    concurrent.futures.Future
                ] = collections.deque()
                remainder_td_ids: t.Deque[int] = collections.deque()
                query = _TagQueryFetchCheckpoint(
                    api, tag_id, fetch_type.from_timestamp, self.until_timestamp
                )

                # Query tags in order on a single thread to prevent overfetching ids
                while query:
                    ids = [i for i in query.next() if i not in seen_td_ids]
                    seen_td_ids.update(ids)
                    remainder_td_ids.extend(ids)
                    while len(remainder_td_ids) >= self.MAX_DESCRIPTOR_FETCH_SIZE:
                        batch = [
                            remainder_td_ids.popleft()
                            for _ in range(self.MAX_DESCRIPTOR_FETCH_SIZE)
                        ]
                        pending_futures.append(
                            id_fetch_pool.submit(
                                self._fetch_descriptors,
                                api,
                                batch,
                                dataset.config.labels,
                            )
                        )
                    if only_first_fetch:
                        break
                    # Consume descriptor data as it becomes available, or if we get too far ahead
                    # to try and avoid a memory explosion
                    while pending_futures and (
                        len(pending_futures) > 200 or pending_futures[0].done()
                    ):
                        consume_descriptors(pending_futures)
                        # TODO Some kind of checkpointing behavior
                # Submit any stragglers
                if remainder_td_ids:
                    pending_futures.append(
                        id_fetch_pool.submit(
                            self._fetch_descriptors,
                            api,
                            list(remainder_td_ids),
                            dataset.config.labels,
                        )
                    )
                while pending_futures:
                    consume_descriptors(pending_futures)

        if fetch_type.is_full and not counts:
            raise command_base.CommandError(
                "No items fetched! Something wrong?", returncode=3
            )
        del counts["all"]  # Not useful for final display

        for signal_name, signal_type in self.signal_types_by_name.items():
            if signal_name not in counts:
                continue
            dataset.store_cache(signal_type)
            print(f"{signal_name}: {counts[signal_name]}")
        if errors:
            self.stderr("\nSome signal types had errors:")
            for signal_name, error_count in sorted(errors.items(), key=lambda t: -t[1]):
                self.stderr(f"  {signal_name}: {error_count}")
        if not self.sample:
            dataset.record_fetch_checkpoint(
                self.until_timestamp or fetch_type.from_timestamp, fetch_type.is_full
            )

    def _fetch_descriptors(
        self, api: ThreatExchangeAPI, td_ids: t.List[int], collab_labels: t.List[str]
    ) -> t.List[ThreatDescriptor]:
        """Do the bulk ThreatDescriptor fetch"""
        return [
            ThreatDescriptor.from_te_json(ThreatDescriptor.MY_APP_ID, td_json)
            for td_json in api.get_threat_descriptors(td_ids)
        ]


class _TagQueryFetchCheckpoint:
    def __init__(
        self, api: ThreatExchangeAPI, tag_id: int, since: float = 0, until: float = 0
    ) -> None:
        self.api = api
        query = {"access_token": api.api_token, "limit": 1000, "fields": "id,type"}
        # Surprise! The endpoint accepts since/until but then ignores them!
        # You must know the secret command words are "tagged_since" and "tagged_until"
        if since:
            query["tagged_since"] = int(since)
        if until:
            query["tagged_until"] = int(until)
        query_str = urllib.parse.urlencode(query)
        # TODO - clean this up, consider making cursoring from a helper object in api
        self._next_url = f"{api._TE_BASE_URL}/{tag_id}/tagged_objects/?{query_str}"

    def __bool__(self) -> bool:
        return bool(self._next_url)

    def next(self) -> t.List:
        response = self.api.get_json_from_url(self._next_url)
        self._next_url = response.get("paging", {}).get("next")
        return [d["id"] for d in response["data"] if d["type"] == "THREAT_DESCRIPTOR"]
