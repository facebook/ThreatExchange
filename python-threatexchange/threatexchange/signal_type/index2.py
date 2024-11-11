import typing as t
import faiss
import pickle
import numpy as np

from threatexchange.signal_type.index import (
    IndexMatchUntyped,
    SignalSimilarityInfoWithIntDistance,
    SignalTypeIndex,
    T as IndexT,
    SignalSimilarityInfo,
    IndexMatch,
)

T = t.TypeVar("T")
DEFAULT_MATCH_DIST = 31
DIMENSIONALITY = 256


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


Self = t.TypeVar("Self", bound="SignalTypeIndex2")

PDQIndexMatch = IndexMatchUntyped[SignalSimilarityInfoWithIntDistance, IndexT]


class SignalTypeIndex2(t.Generic[T]):
    def __init__(
        self,
        threshold: int = DEFAULT_MATCH_DIST,
        faiss_index: t.Optional[faiss.Index] = None,
    ) -> None:
        """
        Initialize the PDQ index.

        Args:
            threshold (int): The maximum distance threshold for matches.
            faiss_index (faiss.Index): An optional pre-existing FAISS index to use.
        """
        super().__init__()
        if faiss_index is None:
            # Use a simple brute-force FAISS index by default
            faiss_index = faiss.IndexFlatL2(DIMENSIONALITY)
        self.faiss_index = _PDQHashIndex(faiss_index)
        self.threshold = threshold
        self._deduper: t.Set[str] = set()
        self._entries: t.List[t.List[T]] = []

    def query(self, query: str) -> t.List[PDQIndexMatch[T]]:
        results = self.faiss_index.search([query], self.threshold)
        return [
            PDQIndexMatch(
                SignalSimilarityInfoWithIntDistance(distance=int(distf)), entry
            )
            for idx, distf in results[0]
            for entry in self._entries[idx]
        ]

    def add(self, pdq_hash: str, entry: T) -> None:
        """
        Add a PDQ hash and its associated entry to the index.

        Args:
            pdq_hash (str): The PDQ hash string
            entry (T): The associated entry data
        """
        if pdq_hash not in self._deduper:
            self._deduper.add(pdq_hash)
            self.faiss_index.add([pdq_hash])
            self._entries.append([entry])
        else:
            # If hash exists, append entry to existing entries
            idx = list(self._deduper).index(pdq_hash)
            self._entries[idx].append(entry)

    def serialize(self, fout: t.BinaryIO) -> None:
        """
        Serialize the PDQ index to a binary stream.
        """
        fout.write(pickle.dumps(self))

    @classmethod
    def deserialize(cls, fin: t.BinaryIO) -> "SignalTypeIndex2[T]":
        """
        Deserialize a PDQ index from a binary stream.
        """
        return pickle.loads(fin.read())
