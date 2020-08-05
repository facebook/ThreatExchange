#!/usr/bin/env python

"""
A command to fetch datasets from ThreatExchange based on the collab config
"""

import argparse
import collections
import concurrent.futures
import inspect
import pathlib
import time
import typing as t
import urllib.parse

from .. import TE
from ..collab_config import CollaborationConfig
from ..content_type import meta
from ..dataset import Dataset
from ..descriptor import ThreatDescriptor
from . import command_base


class FetchCommand(command_base.Command):
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

    def __init__(self, sample: bool, clear: bool = False) -> None:
        """Has default arguments because it's called by match command"""
        self.sample = sample
        self.clear = clear
        self.last_update_printed = time.time()

    def execute(self, dataset: Dataset) -> None:
        if self.clear:
            dataset.clear_cache()
            return
        if self.sample and not dataset.is_cache_empty:
            raise command_base.CommandError(
                "Already have some data, force a refetch by doing --clear", returncode=2
            )

        # TODO - use in with block
        id_fetch_pool = concurrent.futures.ThreadPoolExecutor(max_workers=100)

        seen_td_ids = set()

        signal_types = {clss.get_name(): clss() for clss in meta.get_all_signal_types()}

        counts = collections.Counter()

        tags_to_fetch = dataset.config.labels
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
                match = False
                for signal_name, signal_type in signal_types.items():
                    if signal_type.process_descriptor(descriptor):
                        match = True
                        counts[signal_name] += 1
                if match:
                    counts["all"] += 1
            now = time.time()
            if now - self.last_update_printed >= 30:
                self.last_update_printed = now
                self.stderr(f"Processed {counts['all']}...")
            return len(descriptors)

        for tag_name in tags_to_fetch:
            tag_id = TE.Net.getTagIDFromName(tag_name)
            if not tag_id:
                continue
            pending_futures = collections.deque()
            remainder_td_ids = collections.deque()
            query = _TagQueryFetchCheckpoint(tag_id)

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
                        id_fetch_pool.submit(self._fetch_descriptors, batch)
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
            pending_futures.append(
                id_fetch_pool.submit(self._fetch_descriptors, list(remainder_td_ids))
            )
            while pending_futures:
                consume_descriptors(pending_futures)

        id_fetch_pool.shutdown()
        if not counts:
            raise command_base.CommandError(
                "No items fetched! Something wrong?", returncode=3
            )
        del counts["all"]  # Not useful for final display

        for signal_name, signal_type in signal_types.items():
            if signal_name not in counts:
                continue
            dataset.store_cache(signal_type)
            print(f"{signal_name}: {counts[signal_name]}")

    def _fetch_descriptors(self, td_ids: t.List[int]) -> t.List[ThreatDescriptor]:
        """Do the bulk ThreatDescriptor fetch"""
        return [
            ThreatDescriptor(
                id=int(td["id"]),
                raw_indicator=td["raw_indicator"],
                indicator_type=td["type"],
                owner_id=int(td["owner"]["id"]),
                tags=td["tags"] or [],
                status=td["status"],
                added_on=td["added_on"],
            )
            for td in TE.Net.getInfoForIDs(td_ids)
        ]


class _TagQueryFetchCheckpoint:
    def __init__(self, tag_id: int) -> None:
        query = urllib.parse.urlencode(
            {"access_token": TE.Net.APP_TOKEN, "limit": 1000, "fields": "id,type"}
        )
        self._next_url = f"{TE.Net.TE_BASE_URL}/{tag_id}/tagged_objects/?{query}"

    def __bool__(self) -> bool:
        return bool(self._next_url)

    def next(self) -> t.Dict[id, t.Any]:
        response = TE.Net.getJSONFromURL(self._next_url)
        self._next_url = response.get("paging", {}).get("next")
        return [
            d["id"] for d in response["data"] if d["type"] == TE.Net.THREAT_DESCRIPTOR
        ]
