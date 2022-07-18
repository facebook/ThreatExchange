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


class VPDQFlatIndex(SignalTypeIndex):
    """
    Wrapper around the vpdq faiss index lib using VPDQFlatHashIndex
    """

    @classmethod
    def get_match_threshold(cls) -> int:
        return 31  # VPDQ_CONFIDENT_MATCH_THRESHOLD

    @classmethod
    def _get_empty_index(self) -> VPDQFlatHashIndex:
        return VPDQFlatHashIndex()

    def __init__(self, entries: t.Iterable[t.Tuple[str, IndexT]] = ()) -> None:
        super().__init__()
        self.index: VPDQFlatHashIndex = self._get_empty_index()
        self.add_all(entries=entries)

    def query(self, hash: str) -> t.List[IndexMatch[IndexT]]:
        """
        Look up entries against the index, up to the max supported distance.
        """

        # query takes a signal hash but index supports batch queries hence [hash]
        features = json_to_vpdq(hash)
        results = self.index.search_with_distance_in_result(
            features, self.get_match_threshold()
        )
        res = []
        for feature in features:
            matches = results[feature.hex]
            for match in matches:
                res.append(IndexMatch(match[6], match[0:6]))
        return res

    def add(self, signal_str: str, entry: IndexT) -> None:
        self.index.add_single_video(json_to_vpdq(signal_str), entry)

    def add_all(self, entries: t.Iterable[t.Tuple[str, IndexT]]) -> None:
        for signal_str, entry in entries:
            self.add(signal_str, entry)
