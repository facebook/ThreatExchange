# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import vpdq
import faiss
from threatexchange.extensions.vpdq.vpdq_util import (
    BITS_IN_VPDQ,
)
import typing as t
import numpy
import binascii


class VPDQHashIndex:
    """Wrapper around an faiss binary index for use with searching for similar VPDQ features

    The "flat" variant uses an exhaustive search approach that may use less memory than other approaches and may be more
    performant when using larger thresholds for VPDQ similarity.
    """

    def __init__(self) -> None:
        faiss_index = faiss.IndexBinaryFlat(BITS_IN_VPDQ)
        self.faiss_index = faiss_index
        super().__init__()

    def add_single_video(self, hashes: t.Sequence[vpdq.VpdqFeature]) -> None:
        """
        Args:
            hashes : One video's VPDQ features of to create the index with
        """
        hex_hashes = [h.hex for h in hashes]
        hash_bytes = [binascii.unhexlify(h) for h in hex_hashes]
        vectors = [numpy.frombuffer(h, dtype=numpy.uint8) for h in hash_bytes]
        self.faiss_index.add(numpy.array(vectors))

    def search_with_distance_in_result(
        self, queries: t.Sequence[vpdq.VpdqFeature], distance_tolerance: int
    ) -> t.Dict[str, t.List]:
        """
        Searches this index for PDQ hashes within the index that are no more than the threshold away
        from the query hashes by hamming distance.

        Args:
            queries : The VPDQ features to against the index
            distance_tolerance : Threshold value to use for this search. The hamming distance between the result hashes
            and the related query will be no more than the threshold value. i.e., hamming_dist(q_i,r_i_j) <= threshold.

        Returns:
        sequence of matches per query
            For each query provided in queries, the returned sequence will contain a sequence of matches within the index
            that were within threshold hamming distance of that query. These matches will be (idx, distance).
            The inner sequences may be empty in the case of no hashes within the index.
            The same VPDQ feature may also appear in more than one inner sequence if it matches multiple query hashes.
            For example the hash "000000000000000000000000000000000000000000000000000000000000ffff" would match both
            "00000000000000000000000000000000000000000000000000000000fffffff" and
            "0000000000000000000000000000000000000000000000000000000000000000" for a threshold of 16. Thus it would appear in
            the entry for both the hashes if they were both in the queries list.

            eg.
            query_str =>  (idx, distance)
            result = {
                "000000000000000000000000000000000000000000000000000000000000ffff": [
                    (12345678901, 16.0)
                ]
            }
        """

        query_vectors = [
            numpy.frombuffer(binascii.unhexlify(q.hex), dtype=numpy.uint8)
            for q in queries
        ]
        qs = numpy.array(query_vectors)
        limits, similarities, neighbors = self.faiss_index.range_search(
            qs, distance_tolerance + 1
        )

        result = {}
        for i, query in enumerate(queries):
            matches = [idx.item() for idx in neighbors[limits[i] : limits[i + 1]]]
            distances = [idx for idx in similarities[limits[i] : limits[i + 1]]]
            result[query.hex] = list(zip(matches, distances))
        return result
