##!/usr/bin/env python

import argparse
import collections
import pathlib
import typing as t
import urllib.parse

import TE

from ..collab_config import CollaborationConfig
from ..content_type import meta
from ..dataset import Dataset
from ..descriptor import ThreatDescriptor
from . import base


class FetchCommand(base.Command):
    """
    Download content to save time on future matching.
    """

    @classmethod
    def init_argparse(cls, ap) -> None:
        ap.add_argument(
            "--sample",
            action="store_true",
            help="Only fetch a sample of data instead of the whole dataset",
        )

    @classmethod
    def init_from_namespace(cls, ns) -> "FetchCommand":
        return cls(ns.sample)

    def __init__(self, sample: bool) -> None:
        self.sample = sample

    def execute(self, dataset: Dataset) -> None:
        signal_types = {clss.get_name(): clss() for clss in meta.get_all_signal_types()}

        counts = collections.Counter()

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
                if self.sample:
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
