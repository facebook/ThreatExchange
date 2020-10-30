# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import typing as t
import faiss  # type: ignore
import binascii
import numpy  # type: ignore
from abc import ABC, abstractmethod

BITS_IN_PDQ = 256

PDQ_HASH_TYPE = t.Union[str, bytes]


class PDQHashIndex(ABC):
    @abstractmethod
    def __init__(self, faiss_index: faiss.IndexBinary) -> None:
        self.faiss_index = faiss_index
        super().__init__()

    @abstractmethod
    def hash_at(self, idx: int):
        """
        Returns the hash located at the given index. The index order is determined by the initial order of hashes used to
        create this index.
        """
        pass

    def search(self, queries: t.Sequence[PDQ_HASH_TYPE], threshhold: int):
        """
        Searches this index for PDQ hashes within the index that are no more than the threshold away from the query hashes by
        hamming distance.

        Parameters
        ----------
        queries: sequence of PDQ Hashes
            The PDQ hashes to query against the index
        threshold: int
            Threshold value to use for this search. The hamming distance between the result hashes and the related query will
            be no more than the threshold value. i.e., hamming_dist(q_i,r_i_j) <= threshold.

        Returns
        -------
        sequence of PDQ matches per query
            For each query provided in queries, the returned sequence will contain a sequence of PDQ hashes within the index
            that were within threshold hamming distance of that query. These inner sequences may be empty in the case of no
            hashes within the index. The same PDQ hash may also appear in more than one inner sequence if it matches multiple
            query hashes. For example the hash "000000000000000000000000000000000000000000000000000000000000FFFF" would match
            both "00000000000000000000000000000000000000000000000000000000FFFFFFFF" and
            "0000000000000000000000000000000000000000000000000000000000000000" for a threshold of 16. Thus it would appear in
            the entry for both the hashes if they were both in the queries list.
        """
        query_vectors = [
            numpy.frombuffer(binascii.unhexlify(q), dtype=numpy.uint8) for q in queries
        ]
        qs = numpy.array(query_vectors)
        limits, _, I = self.faiss_index.range_search(qs, threshhold + 1)
        return [
            [self.hash_at(idx.item()) for idx in I[limits[i] : limits[i + 1]]]
            for i in range(len(query_vectors))
        ]


class PDQFlatHashIndex(PDQHashIndex):
    """
    Wrapper around an faiss binary index for use with searching for similar PDQ hashes

    The "flat" variant uses an exhaustive search approach that may use less memory than other approaches and may be more
    performant when using larger thresholds for PDQ similarity.
    """

    def __init__(self, faiss_index: faiss.IndexBinaryFlat):
        super().__init__(faiss_index)

    @staticmethod
    def create(hashes: t.Iterable[PDQ_HASH_TYPE]) -> "PDQFlatHashIndex":
        """
        Creates a PDQFlatHashIndex for use searching against the provided hashes.
        """
        hash_bytes = [binascii.unhexlify(hash) for hash in hashes]
        vectors = list(
            map(lambda h: numpy.frombuffer(h, dtype=numpy.uint8), hash_bytes)
        )
        index = faiss.index_binary_factory(BITS_IN_PDQ, "BFlat")
        index.add(numpy.array(vectors))
        return PDQFlatHashIndex(index)

    def hash_at(self, idx: int):
        vector = self.faiss_index.reconstruct(idx)
        return binascii.hexlify(vector.tobytes()).decode()


class PDQMultiHashIndex(PDQHashIndex):
    """
    Wrapper around an faiss binary index for use with searching for similar PDQ hashes

    The "multi" variant uses an the Multi-Index Hashing searching technique employed by faiss's
    IndexBinaryMultiHash binary index.
    """

    def __init__(self, faiss_index: faiss.IndexBinaryMultiHash):
        super().__init__(faiss_index)

    @staticmethod
    def create(
        hashes: t.Iterable[PDQ_HASH_TYPE], nhash: int = 16
    ) -> "PDQFlatHashIndex":
        """
        Creates a PDQMultiHashIndex for use searching against the provided hashes.

        Parameters
        ----------
        hashes: sequence of PDQ Hashes
            The PDQ hashes to create the index with
        nhash: int (optional)
            Optional number of hashmaps for the underlaying faiss index to use for
            the Multi-Index Hashing lookups.

        Returns
        -------
        a PDQFlatHashIndex of these hashes
        """
        hash_bytes = [binascii.unhexlify(hash) for hash in hashes]
        vectors = list(
            map(lambda h: numpy.frombuffer(h, dtype=numpy.uint8), hash_bytes)
        )
        bits_per_hashmap = BITS_IN_PDQ // nhash
        index = faiss.IndexBinaryMultiHash(BITS_IN_PDQ, nhash, bits_per_hashmap)
        index.add(numpy.array(vectors))
        return PDQMultiHashIndex(index)

    def search(self, queries: t.Sequence[PDQ_HASH_TYPE], threshhold: int):
        self.faiss_index.nflip = threshhold // self.faiss_index.nhash
        return super().search(queries, threshhold)

    def hash_at(self, idx: int):
        vector = self.faiss_index.storage.reconstruct(idx)
        return binascii.hexlify(vector.tobytes()).decode()
