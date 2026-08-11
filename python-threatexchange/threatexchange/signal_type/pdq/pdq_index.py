# Copyright (c) Meta Platforms, Inc. and affiliates.

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
        # FAISS returns integer vector ids; this maps those ids to match metadata.
        # Do not store the PDQ hex here — it is already held in the FAISS index.
        self.local_id_to_entry: t.List[IndexT] = []
        self.index: PDQHashIndex = self._get_empty_index()
        self.add_all(entries=entries)

    def __setstate__(self, state: t.Dict[str, t.Any]) -> None:
        # Older indexes stored (pdq_hex, entry) tuples; matching only needs entry.
        entries = state.get("local_id_to_entry")
        if (
            isinstance(entries, list)
            and entries
            and isinstance(entries[0], tuple)
            and len(entries[0]) == 2
            and isinstance(entries[0][0], str)
        ):
            state = {
                **state,
                "local_id_to_entry": [entry[1] for entry in entries],
            }
        self.__dict__.update(state)

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
                    self.local_id_to_entry[id],
                )
            )
        return matches

    def add(self, signal_str: str, entry: IndexT) -> None:
        self.add_all(((signal_str, entry),))

    def add_all(self, entries: t.Iterable[t.Tuple[str, IndexT]]) -> None:
        start = len(self.local_id_to_entry)
        batch_signals: t.List[str] = []
        for signal_str, entry in entries:
            batch_signals.append(signal_str)
            self.local_id_to_entry.append(entry)
        if batch_signals:
            self.index.add(
                batch_signals,
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
