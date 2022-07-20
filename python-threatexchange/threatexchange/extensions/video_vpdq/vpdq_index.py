# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Implementation of SignalTypeIndex abstraction for PDQ by wrapping
hashing.pdq_faiss_matcher.
"""

import typing as t
import vpdq
from threatexchange.signal_type.index import (
    SignalTypeIndex,
    IndexMatch,
    T as IndexT,
)
from threatexchange.extensions.video_vpdq.vpdq_faiss_matcher import VPDQFlatHashIndex
from threatexchange.extensions.video_vpdq.vpdq_util import (
    prepare_vpdq_feature,
    VPDQMatchResult,
)


class VPDQIndex(SignalTypeIndex):
    """
    Wrapper around the vpdq faiss index lib using VPDQFlatHashIndex
    """

    @classmethod
    def get_match_distance_threshold(cls) -> int:
        return 31  ##VPDQ_CONFIDENT_DISTANCE_THRESHOLD

    @classmethod
    def get_match_quality_threshold(cls) -> int:
        return 50  ##VPDQ_CONFIDENT_QUALITY_THRESHOLD

    @classmethod
    def _get_empty_index(cls) -> VPDQFlatHashIndex:
        return VPDQFlatHashIndex()

    def __init__(self, entries: t.Iterable[t.Tuple[str, IndexT]] = ()) -> None:
        super().__init__()
        self.index: VPDQFlatHashIndex = self._get_empty_index()
        self.entries: t.List = []
        self.idx_to_vpdq: t.List[t.Tuple[int, vpdq.VpdqFeature]] = []
        self.video_length = []
        self.add_all(entries=entries)

    def add(self, signal_str: str, entry: IndexT) -> None:
        entry_id = len(self.entries)
        features = prepare_vpdq_feature(signal_str, self.get_match_quality_threshold())
        self.entries.append(entry)
        self.idx_to_vpdq.extend([(entry_id, f) for f in features])
        self.video_length.append(len(features))
        self.index.add_single_video(features)

    def query(self, hash: str) -> t.List[IndexMatch[IndexT]]:
        """
        Look up entries against the index, up to the max supported distance.
        """

        # query takes a signal hash but index supports batch queries hence [hash]
        results = self.query_with_match_percentage_in_result(hash)
        matches = []
        for match in results:
            entry_id, match_result = match
            max_percent = max(
                match_result.query_match_percent, match_result.compared_match_percent
            )
            matches.append(IndexMatch(int(max_percent), self.entries[entry_id]))
        return matches

    def query_raw_result(self, query_hash: str) -> t.Dict[str, t.List]:
        features = prepare_vpdq_feature(query_hash, self.get_match_quality_threshold())
        results = self.index.search_with_raw_features_in_result(
            features, self.get_match_distance_threshold()
        )
        matches = {}
        for hash in results:
            match_tuples = []
            for match in results[hash]:
                entry_id, vpdq_match = self.idx_to_vpdq[match[0]]
                match_tuples.append([vpdq_match.hex, match[1], self.entries[entry_id]])
            matches[hash] = match_tuples
        return matches

    def query_with_match_percentage_in_result(
        self,
        query_hash: t.List[vpdq.VpdqFeature],
    ) -> t.List[t.Tuple[int, VPDQMatchResult]]:
        """Searches this VPDQ index for query hashes within the index that are no more than the threshold away
        from the query hashes by hamming distance.

        Args:
            query_hash : Query VPDQ hash
            VPDQ_index : VPDQ index to be searched for query hash
            quality_tolerance : The quality tolerance of matching two frames.
            If either frames is below this quality level then they will not be queired and added to result
            distance_tolerance : The hamming distance tolerance of between two frames.
            If the hamming distance is bigger than the tolerance, it will be considered as unmatched

        Returns:
            VPDQ Video id corresponds with its VPDQMatchResult
        """
        features = prepare_vpdq_feature(query_hash, self.get_match_quality_threshold())
        results = self.index.search_with_raw_features_in_result(
            features, self.get_match_distance_threshold()
        )
        query_matched: t.Dict[int, t.Set] = {}
        index_matched: t.Dict[int, t.Set] = {}
        for hash in results:
            for match in results[hash]:
                # query_str =>  (match, entry)
                entry_id, vpdq_match = self.idx_to_vpdq[match[0]]

                if entry_id not in query_matched:
                    query_matched[entry_id] = set()
                query_matched[entry_id].add(hash)

                if entry_id not in index_matched:
                    index_matched[entry_id] = set()
                index_matched[entry_id].add(vpdq_match.frame_number)
        return [
            (
                entry_id,
                VPDQMatchResult(
                    len(query_matched[entry_id]) * 100 / len(features),
                    len(index_matched[entry_id]) * 100 / self.video_length[entry_id],
                ),
            )
            for entry_id in sorted(query_matched)
        ]
