#!/usr/bin/env python

"""
A command to fetch datasets from ThreatExchange based on the collab config
"""

import argparse
import collections
import inspect
import pathlib
import typing as t
import urllib.parse

from .. import TE
from ..collab_config import CollaborationConfig
from ..content_type import meta
from ..dataset import Dataset
from ..descriptor import ThreatDescriptor
from . import base


class FetchCommand(base.Command):
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

    def execute(self, dataset: Dataset) -> None:
        if self.clear:
            dataset.clear_cache()
            return
        signal_types = {clss.get_name(): clss() for clss in meta.get_all_signal_types()}

        counts = collections.Counter()

        tags_to_fetch = dataset.config.labels
        only_first_fetch = False

        if self.sample:
            if dataset.config.sample_tag:
                tags_to_fetch = [dataset.config.sample_tag]
            else:
                only_first_fetch = True

        for tag_name in dataset.config.labels:
            tag_id = TE.Net.getTagIDFromName(tag_name)
            if not tag_id:
                continue
            query = _TagQueryFetchCheckpoint(tag_id)
            while query:
                descriptors = query.next()
                for td in descriptors:
                    descriptor = ThreatDescriptor(
                        id=int(td["id"]),
                        raw_indicator=td["raw_indicator"],
                        indicator_type=td["type"],
                        owner_id=int(td["owner"]["id"]),
                        tags=td["tags"] or [],
                        status=td["status"],
                        added_on=td["added_on"],
                    )
                    for signal_name, signal_type in signal_types.items():
                        if signal_type.process_descriptor(descriptor):
                            counts[signal_name] += 1
                if only_first_fetch:
                    break
        if not counts:
            raise base.CommandError("No items fetched! Something wrong?", returncode=3)

        for signal_name, signal_type in signal_types.items():
            if signal_name not in counts:
                continue
            dataset.store_cache(signal_type)
            print(f"{signal_name}: {counts[signal_name]}")


class _TagQueryFetchCheckpoint:
    def __init__(self, tag_id: int) -> None:
        query = urllib.parse.urlencode({"access_token": TE.Net.APP_TOKEN, "limit": 50})
        self._next_url = f"{TE.Net.TE_BASE_URL}/{tag_id}/tagged_objects/?{query}"

    def __bool__(self) -> bool:
        return bool(self._next_url)

    def next(self) -> t.Dict[id, t.Any]:
        response = TE.Net.getJSONFromURL(self._next_url)
        self._next_url = response.get("paging", {}).get("next")
        ids = [
            d["id"] for d in response["data"] if d["type"] == TE.Net.THREAT_DESCRIPTOR
        ]
        if not ids:
            return []
        return TE.Net.getInfoForIDs(ids)
