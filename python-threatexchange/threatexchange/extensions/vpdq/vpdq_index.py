# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Implementation of SignalTypeIndex abstraction for PDQ by wrapping
hashing.pdq_faiss_matcher.
"""

import typing as t
import vpdq
from threatexchange.signal_type.index import (
    PickledSignalTypeIndex,
    VPDQIndexMatch,
    IndexMatch,
    T as IndexT,
)
from threatexchange.extensions.vpdq.vpdq_faiss import VPDQHashIndex
from threatexchange.extensions.vpdq.vpdq_util import (
    prepare_vpdq_feature,
    VPDQ_QUALITY_THRESHOLD,
    VPDQ_DISTANCE_THRESHOLD,
)


class VPDQIndex(PickledSignalTypeIndex[IndexT]):
    """
    Wrapper around the vpdq faiss index lib using VPDQHashIndex
    """

    def __init__(
        self,
        quality_threshold: int = VPDQ_QUALITY_THRESHOLD,
    ) -> None:
        super().__init__()
        self.index: VPDQHashIndex = VPDQHashIndex()
        self.entry_idx_to_features_and_entires: t.List[
            t.Tuple[t.List[vpdq.VpdqFeature], IndexT]
        ] = []
        self.index_idx_to_vpdqFrame: t.List[t.Tuple[int, int]] = []
        self.quality_threshold = quality_threshold

    def add(self, signal_str: str, entry: IndexT) -> None:
        entry_id = len(self.entry_idx_to_features_and_entires)
        features = prepare_vpdq_feature(signal_str, self.quality_threshold)
        self.entry_idx_to_features_and_entires.append((features, entry))
        # Use frame_number to represent the feature because it is guaranteed to be unique within each video(entry_id)
        self.index_idx_to_vpdqFrame.extend((entry_id, f.frame_number) for f in features)
        self.index.add_single_video(features)

    def query(self, query_hash: str) -> t.List[IndexMatch[IndexT]]:
        """Searches this VPDQ index for query hashes within the index that are no more than the threshold away
        from the query hashes by hamming distance.

        Args:
            query_hash : Query VPDQ hash

        Returns:
            List of VPDQIndexMatch
        """
        features = prepare_vpdq_feature(query_hash, self.quality_threshold)
        results = self.index.search_with_distance_in_result(
            features, VPDQ_DISTANCE_THRESHOLD
        )
        query_matched: t.Dict[int, t.Set[str]] = {}
        index_matched: t.Dict[int, t.Set[int]] = {}
        matches: t.List[IndexMatch[IndexT]] = []
        for hash in results:
            for match in results[hash]:
                # query_str =>  (matched_idx, distance)
                entry_id, vpdq_match = self.index_idx_to_vpdqFrame[match[0]]
                if entry_id not in query_matched:
                    query_matched[entry_id] = set()
                query_matched[entry_id].add(hash)

                if entry_id not in index_matched:
                    index_matched[entry_id] = set()
                index_matched[entry_id].add(vpdq_match)
        # Dist(-1) is meaningless here, because VPDQ match does not return a single dist
        matches.append(
            VPDQIndexMatch(
                -1,
                len(query_matched[entry_id]) * 100 / len(features),
                len(index_matched[entry_id])
                * 100
                / len(self.entry_idx_to_features_and_entires[entry_id][0]),
                self.entry_idx_to_features_and_entires[entry_id][1],
            )
        )
        return matches
