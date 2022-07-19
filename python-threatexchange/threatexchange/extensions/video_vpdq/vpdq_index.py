# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Implementation of SignalTypeIndex abstraction for PDQ by wrapping
hashing.pdq_faiss_matcher.
"""

import typing as t

from threatexchange.signal_type.index import (
    SignalTypeIndex,
    IndexMatch,
    T as IndexT,
)

from threatexchange.extensions.video_vpdq.vpdq_faiss_matcher import VPDQFlatHashIndex
from threatexchange.extensions.video_vpdq.vpdq_util import json_to_vpdq
from threatexchange.extensions.video_vpdq.video_vpdq import VideoVPDQSignal

VIDEO_ID = "video_id"


class VPDQFlatIndex(SignalTypeIndex):
    """
    Wrapper around the vpdq faiss index lib using VPDQFlatHashIndex
    """

    @classmethod
    def get_match_threshold(cls) -> int:
        return VideoVPDQSignal.VPDQ_CONFIDENT_DISTANCE_THRESHOLD

    @classmethod
    def _get_empty_index(self) -> VPDQFlatHashIndex:
        return VPDQFlatHashIndex()

    def __init__(self, entries: t.Iterable[t.Tuple[str, t.Dict]] = ()) -> None:
        super().__init__()
        self.index: VPDQFlatHashIndex = self._get_empty_index()
        self.video_id_to_entry: t.Dict = {}
        self.add_all(entries=entries)

    def query(self, hash: str) -> t.List[IndexMatch[IndexT]]:
        """
        Look up entries against the index, up to the max supported distance.
        """

        # query takes a signal hash but index supports batch queries hence [hash]
        features = json_to_vpdq(hash)
        results = self.index.search_with_match_percentage_in_result(
            features,
            VideoVPDQSignal.VPDQ_CONFIDENT_QUALITY_THRESHOLD,
            VideoVPDQSignal.VPDQ_CONFIDENT_DISTANCE_THRESHOLD,
        )
        matches = []
        for match in results:
            match_result = match[1]
            max_percent = max(
                match_result.query_match_percent, match_result.compared_match_percent
            )
            matches.append(
                IndexMatch(int(max_percent), self.video_id_to_entry[match[0]])
            )
        return matches

    def query_raw_result(self, hash: str) -> t.Dict[str, t.List]:
        features = json_to_vpdq(hash)
        results = self.index.search_with_raw_features_in_result(
            features, self.get_match_threshold()
        )
        return results

    def add(self, signal_str: str, entry: t.Dict) -> None:
        if entry[VIDEO_ID] is None:
            raise ValueError("invalid VPDQ entry, this must exist a video_id")
        video_id = entry[VIDEO_ID]
        self.video_id_to_entry[video_id] = entry
        self.index.add_single_video(json_to_vpdq(signal_str), video_id)

    def add_all(self, entries: t.Iterable[t.Tuple[str, t.Dict]]) -> None:
        for signal_str, entry in entries:
            self.add(signal_str, entry)
