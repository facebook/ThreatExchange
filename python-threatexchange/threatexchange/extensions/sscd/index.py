"""
TODO
"""

import typing as t

import numpy
import faiss
import json

from threatexchange.signal_type.index import (
    IndexMatch,
    T,
    Self,
    SignalSimilarityInfoWithSingleDistance,
    SignalTypeIndex,
)

DIMENSIONALITY = 512


def sscd_signal_strs_to_ndarray(hashes: t.Sequence[str]) -> numpy.ndarray:
    """
    Convert decimal, comma-separated strings into ndarrays for faiss.
    """
    return numpy.ndarray(
        (len(hashes), DIMENSIONALITY),
        dtype=numpy.float32,
        buffer=numpy.fromiter(
            (x for j in hashes for x in json.loads(j)), dtype=numpy.float32
        ),
    )


class _SSCDHashIndex:
    """
    A wrapper around the faiss index for pickle serialization
    """

    def __init__(self, faiss_index: faiss.Index) -> None:
        self.faiss_index = faiss_index

    def search(
        self,
        queries: t.Sequence[str],
        threshhold: int,
    ) -> t.List[t.Tuple[int, float]]:
        """
        Search method that return a mapping from query_str =>  (id, distance)
        """
        qs = sscd_signal_strs_to_ndarray(queries)
        limits, D, I = self.faiss_index.range_search(qs, threshhold)

        results = []
        for i in range(len(queries)):
            matches = [result.item() for result in I[limits[i] : limits[i + 1]]]
            distances = [dist for dist in D[limits[i] : limits[i + 1]]]
            results.append(list(zip(matches, distances)))
        return results

    def __getstate__(self):
        data = faiss.serialize_index(self.faiss_index)
        return data

    def __setstate__(self, data):
        self.faiss_index = faiss.deserialize_index(data)


class SSCDSignalTypeIndex(SignalTypeIndex[T]):
    def __init__(
        self,
        threshold: float = 0.5,
        faiss_index: t.Optional[faiss.Index] = None,
    ) -> None:
        super().__init__()
        if faiss_index is None:
            # Brute force
            faiss_index = faiss.IndexFlatL2(DIMENSIONALITY)
        self.faiss_index = _SSCDHashIndex(faiss_index)
        self.threshold = threshold
        self._deduper = {}
        self._idx_to_entries: t.List[t.List[T]] = []

    def query(self, query: str) -> t.List[IndexMatch[T]]:
        results = self.faiss_index.search([query], self.threshold)
        return [
            IndexMatch(SignalSimilarityInfoWithSingleDistance(distf), entry)
            for idx, distf in results[0]
            for entry in self._idx_to_entries[idx]
        ]

    def add(self, signal_str: str, entry: T) -> None:
        self._dedupe_and_add(signal_str, entry)

    def _dedupe_and_add(self, signal_str: str, entry: T, *, add_to_faiss=True) -> None:
        idx = self._deduper.get(signal_str)
        if idx is not None:
            self._idx_to_entries[idx].append(entry)
            return
        if add_to_faiss:
            self.faiss_index.faiss_index.add(sscd_signal_strs_to_ndarray([signal_str]))
        self._deduper[signal_str] = len(self._idx_to_entries)
        self._idx_to_entries.append([entry])

    @classmethod
    def build(cls: t.Type[Self], entries: t.Iterable[t.Tuple[str, T]]) -> Self:
        """
        Faiss has many potential options that we can choose based on the size of the index.
        """
        entry_list = list(entries)
        # From sscd github
        if len(entries) < 1024:
            return super().build(entry_list)
        index = faiss.index_factory(DIMENSIONALITY, f"PCAW512,L2norm,Flat")
        ret = cls(faiss_index=index)
        for signal_str, entry in entry_list:
            ret._dedupe_and_add(signal_str, entry, add_to_faiss=False)
        xb = sscd_signal_strs_to_ndarray(tuple(s for s in ret._deduper))
        index.train(xb)
        index.add(xb)
        return ret
