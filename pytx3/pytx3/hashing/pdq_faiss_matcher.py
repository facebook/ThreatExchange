import typing as t
import faiss  # type: ignore
import binascii
import numpy  # type: ignore

BITS_IN_PDQ = 256

PDQ_HASH_TYPE = t.Union[str, bytes]


class PDQFlatHashIndex:
    """
    Wrapper around an faiss binary index for use with searching for similar PDQ hashes

    The "flat" variant uses an exhaustive search approach that may use less memory than other approaches and may be more
    performant when using larger thresholds for PDQ similarity.
    """

    def __init__(
        self, faiss_index: faiss.IndexBinaryFlat, dataset_hashes: t.Sequence[bytes]
    ) -> None:
        self.faiss_index = faiss_index
        self.dataset_hashes = dataset_hashes

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
        return PDQFlatHashIndex(index, hash_bytes)

    def search(
        self, queries: t.Sequence[PDQ_HASH_TYPE], threshhold: int
    ) -> t.Sequence[t.Sequence[str]]:
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
            [
                binascii.hexlify(self.dataset_hashes[idx]).decode()
                for idx in I[limits[i] : limits[i + 1]]
            ]
            for i in range(len(query_vectors))
        ]
