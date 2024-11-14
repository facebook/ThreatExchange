# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Implementation of SignalTypeIndex abstraction for PDQ by wrapping
hashing.pdq_faiss_matcher.
"""

import typing as t
import faiss
import numpy as np
import pickle


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

DEFAULT_MATCH_DIST = 31
DIMENSIONALITY = 256

PDQIndexMatch = IndexMatchUntyped[SignalSimilarityInfoWithIntDistance, IndexT]


class PDQIndex2(SignalTypeIndex[IndexT]):
    """
    Wrapper around the pdq faiss index lib using PDQMultiHashIndex
    """

    def __init__(
        self,
        threshold: int = DEFAULT_MATCH_DIST,
        index: t.Optional[faiss.Index] = None,
        entries: t.Iterable[t.Tuple[str, IndexT]] = (),
    ) -> None:
        super().__init__()
        self.threshold = threshold

        if index is None:
            index = faiss.IndexFlatL2(DIMENSIONALITY)
        self.index = _PDQHashIndex(index)

        # Matches hash to Faiss index
        self._deduper: t.Dict[str, faiss.IndexFlatL2] = {}
        # Entry mapping: Each list[entries]'s index is its hash's index
        self._idx_to_entries: t.List[t.List[IndexT]] = []

        self.add_all(entries=entries)

    def __len__(self) -> int:
        return len(self._idx_to_entries)

    def query(self, hash: str) -> t.Sequence[PDQIndexMatch[IndexT]]:
        """
        Look up entries against the index, up to the max supported distance.
        """
        results: t.List[PDQIndexMatch[IndexT]] = []
        matches_list: t.List[t.List[t.Any]] = self.index.search(
            queries=[hash], threshold=self.threshold
        )

        for matches in matches_list:
            for match_hash, distance in matches:
                entries = self._idx_to_entries[match_hash]  # Get the Faiss index
                # Create match objects for each entry
                results.extend(
                    PDQIndexMatch(
                        SignalSimilarityInfoWithIntDistance(distance=int(distance)),
                        entry,
                    )
                    for entry in entries
                )
        return results

    def add(self, signal_str: str, entry: IndexT) -> None:
        self.add_all(((signal_str, entry),))

    def add_all(self, entries: t.Iterable[t.Tuple[str, IndexT]]) -> None:
        for h, i in entries:
            existing_faiss_id = self._deduper.get(h)
            if existing_faiss_id is None:
                self.index.add([h])
                self._idx_to_entries.append([i])
                next_id = len(self._deduper)  # Because faiss index starts from 0 up
                self._deduper[h] = next_id
            else:
                # Since this already exists, we don't add it to Faiss because Faiss cannot handle duplication
                self._idx_to_entries[existing_faiss_id].append(h)

    def serialize(self, fout: t.BinaryIO) -> None:
        """
        Serialize the PDQ index to a binary stream.
        """
        fout.write(pickle.dumps(self))

    @classmethod
    def deserialize(cls, fin: t.BinaryIO) -> "PDQIndex2[IndexT]":
        """
        Deserialize a PDQ index from a binary stream.
        """
        return pickle.loads(fin.read())


class _PDQHashIndex:
    """
    A wrapper around the faiss index for pickle serialization
    """

    def __init__(self, faiss_index: faiss.Index) -> None:
        self.faiss_index = faiss_index

    def add(self, pdq_strings: t.Sequence[str]) -> None:
        """
        Add PDQ hashes to the FAISS index.
        Args:
            pdq_strings (Sequence[str]): PDQ hash strings to add
        """
        vectors = self._convert_pdq_strings_to_ndarray(pdq_strings)
        self.faiss_index.add(vectors)

    def search(
        self, queries: t.Sequence[str], threshold: int = DEFAULT_MATCH_DIST
    ) -> t.List[t.List[t.Any]]:
        """
        Search the FAISS index for matches to the given PDQ queries.
        Args:
            queries (Sequence[str]): The PDQ signal strings to search for.
            threshold (int): The maximum distance threshold for matches.
        Returns:
            2D list of tuples that store (matches, distances) for each query
        """
        query_array: np.ndarray = self._convert_pdq_strings_to_ndarray(queries)
        limits, distances, indices = self.faiss_index.range_search(
            query_array, threshold + 1
        )

        results: t.List[t.List[t.Any]] = []
        for i in range(len(queries)):
            matches = [idx.item() for idx in indices[limits[i] : limits[i + 1]]]
            dists = [dist for dist in distances[limits[i] : limits[i + 1]]]
            results.append(list(zip(matches, dists)))
        return results

    def __getstate__(self):
        data = faiss.serialize_index(self.faiss_index)
        return data

    def __setstate__(self, data):
        self.faiss_index = faiss.deserialize_index(data)

    def _convert_pdq_strings_to_ndarray(
        self, pdq_strings: t.Sequence[str]
    ) -> np.ndarray:
        """
        Convert multiple PDQ hash strings to a numpy array.
        Args:
            pdq_strings (Sequence[str]): A sequence of 64-character hexadecimal PDQ hash strings
        Returns:
            np.ndarray: A 2D array of shape (n_queries, 256) where each row is the full PDQ hash as a bit array
        """
        hash_arrays = []
        for pdq_str in pdq_strings:
            print("converting string:", pdq_str)
            try:
                # Convert hex string to integer
                hash_int = int(pdq_str, 16)
                # Convert to binary string, padding to ensure 256 bits
                binary_str = format(hash_int, "0256b")
                # Convert to numpy array
                hash_array = np.array(
                    [int(bit) for bit in binary_str], dtype=np.float32
                )
                hash_arrays.append(hash_array)
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid PDQ hash string: {pdq_str}") from e

        # Convert list of arrays to a single 2D array
        return np.array(hash_arrays, dtype=np.float32)
