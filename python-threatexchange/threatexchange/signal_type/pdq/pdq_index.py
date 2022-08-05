# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Implementation of SignalTypeIndex abstraction for PDQ by wrapping
hashing.pdq_faiss_matcher.
"""

import typing as t

from threatexchange.signal_type.index import (
    IndexMatchUntyped,
    SignalSimilarityInfoWithIntDistance,
    SignalTypeIndex,
    T as IndexT,
)
from threatexchange.signal_type.pdq.pdq_faiss_matcher import (
    PDQMultiHashIndex,
    PDQFlatHashIndex,
    PDQHashIndex,
)

PDQIndexMatch = IndexMatchUntyped[SignalSimilarityInfoWithIntDistance, IndexT]


class PDQIndex(SignalTypeIndex[IndexT]):
    """
    Wrapper around the pdq faiss index lib using PDQMultiHashIndex
    """

    @classmethod
    def get_match_threshold(cls):
        return 31  # PDQ_CONFIDENT_MATCH_THRESHOLD

    @classmethod
    def _get_empty_index(cls) -> PDQHashIndex:
        return PDQMultiHashIndex()

    def __init__(self, entries: t.Iterable[t.Tuple[str, IndexT]] = ()) -> None:
        super().__init__()
        self.local_id_to_entry: t.List[t.Tuple[str, IndexT]] = []
        self.index: PDQHashIndex = self._get_empty_index()
        self.add_all(entries=entries)

    def __len__(self) -> int:
        return len(self.local_id_to_entry)

    def query(self, hash: str) -> t.Sequence[PDQIndexMatch[IndexT]]:
        """
        Look up entries against the index, up to the max supported distance.
        """

        # query takes a signal hash but index supports batch queries hence [hash]
        results = self.index.search_with_distance_in_result(
            [hash], self.get_match_threshold()
        )

        matches = []
        for id, _, distance in results[hash]:
            matches.append(
                IndexMatchUntyped(
                    SignalSimilarityInfoWithIntDistance(int(distance)),
                    self.local_id_to_entry[id][1],
                )
            )
        return matches

    def add(self, signal_str: str, entry: IndexT) -> None:
        self.add_all(((signal_str, entry),))

    def add_all(self, entries: t.Iterable[t.Tuple[str, IndexT]]) -> None:
        start = len(self.local_id_to_entry)
        self.local_id_to_entry.extend(entries)
        if start != len(self.local_id_to_entry):
            # This function signature is very silly
            self.index.add(
                (e[0] for e in self.local_id_to_entry[start:]),
                range(start, len(self.local_id_to_entry)),
            )


class PDQFlatIndex(PDQIndex):
    """
    Wrapper around the pdq faiss index lib
    that uses PDQFlatHashIndex instead of PDQMultiHashIndex
    It also uses a high match threshold to increase recall
    possibly as the cost of precision.
    """

    @classmethod
    def get_match_threshold(cls):
        return 52  # larger PDQ_MATCH_THRESHOLD for flatindexes

    @classmethod
    def _get_empty_index(cls) -> PDQHashIndex:
        return PDQFlatHashIndex()
