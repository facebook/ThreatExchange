# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Implementation of SignalTypeIndex abstraction for VPDQ by wrapping
vpdq_faiss.
"""

import typing as t
import vpdq
from threatexchange.signal_type.index import (
    SignalTypeIndex,
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


class VPDQIndex(SignalTypeIndex[IndexT]):
    """
    Wrapper around the vpdq faiss index lib using VPDQHashIndex
    """

    def __init__(
        self,
        quality_threshold: int = VPDQ_QUALITY_THRESHOLD,
    ) -> None:
        super().__init__()
        self.index: VPDQHashIndex = VPDQHashIndex()
        self._entry_idx_to_features_and_entires: t.List[
            t.Tuple[t.List[vpdq.VpdqFeature], IndexT]
        ] = []
        self._index_idx_to_vpdqHex_and_entry: t.List[t.Tuple[int, t.List[int]]] = []
        self._unique_vpdqHex_to_index_idx: t.Dict[str, int] = {}
        self.quality_threshold = quality_threshold

    def add(self, signal_str: str, entry: IndexT) -> None:
        entry_id = len(self._entry_idx_to_features_and_entires)
        features = prepare_vpdq_feature(signal_str, self.quality_threshold)
        if not features:
            raise ValueError(
                "Empty video after deduping/filtering should not be indexed"
            )
        self._entry_idx_to_features_and_entires.append((features, entry))
        # Use hex to represent the feature because it saves the space
        unique_features = []
        for f in features:
            idx = self._unique_vpdqHex_to_index_idx.get(f.hex)
            if idx is None:
                idx = len(self._unique_vpdqHex_to_index_idx)
                self._unique_vpdqHex_to_index_idx[f.hex] = idx
                self._index_idx_to_vpdqHex_and_entry.append((f.hex, list()))
                unique_features.append(f)
            self._index_idx_to_vpdqHex_and_entry[idx][1].append(entry_id)
        if unique_features:
            self.index.add_single_video(unique_features)

    def query(self, query_hash: str) -> t.List[IndexMatch[IndexT]]:
        """Searches this VPDQ index for query hashes within the index that are no more than the threshold away
        from the query hashes by hamming distance.

        Args:
            query_hash : Query VPDQ hash

        Returns:
            List of VPDQIndexMatch
        """
        features = prepare_vpdq_feature(query_hash, self.quality_threshold)
        if not features:
            return []
        results = self.index.search_with_distance_in_result(
            features, VPDQ_DISTANCE_THRESHOLD
        )
        query_matched: t.Dict[int, t.Set[str]] = {}
        index_matched: t.Dict[int, t.Set[int]] = {}
        matches: t.List[IndexMatch[IndexT]] = []
        for hash in results:
            for match in results[hash]:
                # query_str =>  (matched_idx, distance)
                vpdq_match, entry_list = self._index_idx_to_vpdqHex_and_entry[match[0]]
                for entry_id in entry_list:
                    if entry_id not in query_matched:
                        query_matched[entry_id] = set()
                    query_matched[entry_id].add(hash)

                    if entry_id not in index_matched:
                        index_matched[entry_id] = set()
                    index_matched[entry_id].add(vpdq_match)
        for entry_id in query_matched.keys():
            query_matched_percent = len(query_matched[entry_id]) * 100 / len(features)
            index_matched_percent = (
                len(index_matched[entry_id])
                * 100
                / len(self._entry_idx_to_features_and_entires[entry_id][0])
            )
            # max_matched_percent is returned as dist(int) here for a temporal solution
            # TODO: Make dist attribute internal detail in IndexMatch Class
            max_matched_percent = int(max(query_matched_percent, index_matched_percent))
            matches.append(
                VPDQIndexMatch(
                    max_matched_percent,
                    query_matched_percent,
                    index_matched_percent,
                    self._entry_idx_to_features_and_entires[entry_id][1],
                )
            )
        return matches
