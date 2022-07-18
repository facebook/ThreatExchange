import vpdq
import faiss
from .vpdq_util import dedupe, quality_filter
import typing as t
import numpy
import binascii
from threatexchange.signal_type.index import T as IndexT, IndexMatch

BITS_IN_VPDQ = 256


class VPDQFlatHashIndex:
    """Wrapper around an faiss binary index for use with searching for similar VPDQ features

    The "flat" variant uses an exhaustive search approach that may use less memory than other approaches and may be more
    performant when using larger thresholds for VPDQ similarity.
    """

    def __init__(self) -> None:
        faiss_index = faiss.IndexBinaryFlat(BITS_IN_VPDQ)
        self.faiss_index = faiss_index
        self.idx_to_vpdq = []
        self.video_id_to_vpdq = {}
        super().__init__()

    def get_video_frame_counts(self, video_id: IndexT, quality_tolerance: int) -> int:
        """
        Args:
            video_id
            quality_tolerance
        Returns:
            Size of VPDQ features in the video that has a quality larger or equal to quality_tolerance
        """
        return len(quality_filter(self.video_id_to_vpdq[video_id], quality_tolerance))

    def add_single_video(
        self,
        hashes: t.Iterable[vpdq.VpdqFeature],
        video_id: IndexT,
    ) -> None:
        """
        Args:
            hashes : One video's VPDQ features of to create the index with
            video_id : Unique video id corresponeds to the hashes in a single video
        """
        if video_id in self.video_id_to_vpdq:
            raise ValueError("invalid VPDQ Index Video ID, this ID already exists")
        hashes = dedupe(hashes)
        self.idx_to_vpdq.extend([(video_id, h) for h in hashes])
        self.video_id_to_vpdq[video_id] = hashes
        hex_hashes = [h.hex for h in hashes]
        hash_bytes = [binascii.unhexlify(h) for h in hex_hashes]
        vectors = list(
            map(lambda h: numpy.frombuffer(h, dtype=numpy.uint8), hash_bytes)
        )
        self.faiss_index.add(numpy.array(vectors))

    def search_with_distance_in_result(
        self,
        queries: t.Sequence[vpdq.VpdqFeature],
        threshhold: int,
    ) -> t.List[IndexMatch[IndexT]]:
        """
        Searches this index for PDQ hashes within the index that are no more than the threshold away from the query hashes by
        hamming distance.

        Args:
            queries : The VPDQ features to against the index
            threshold : Threshold value to use for this search. The hamming distance between the result hashes and the related query will
            be no more than the threshold value. i.e., hamming_dist(q_i,r_i_j) <= threshold.

        Returns:
        sequence of matches per query
            For each query provided in queries, the returned sequence will contain a sequence of matches within the index
            that were within threshold hamming distance of that query. These matches will be (id, video_id, frame_number,
            hex_str of hash, quality, distance). The inner sequences may be empty in the case of no hashes within the index.
            The same VPDQ feature may also appear in more than one inner sequence if it matches multiple query hashes.
            For example the hash "000000000000000000000000000000000000000000000000000000000000ffff" would match both
            "00000000000000000000000000000000000000000000000000000000fffffff" and
            "0000000000000000000000000000000000000000000000000000000000000000" for a threshold of 16. Thus it would appear in
            the entry for both the hashes if they were both in the queries list.

            eg.
            query_str =>  (id, video_id, frame_number, hex_str of hash, quality, timestamp, distance)
            result = {
                "000000000000000000000000000000000000000000000000000000000000ffff": [
                    (12345678901, "video1", 38, "00000000000000000000000000000000000000000000000000000000fffffff",97, 0.1, 16.0)
                ]
            }
        """

        queries = dedupe(queries)
        query_vectors = [
            numpy.frombuffer(binascii.unhexlify(q.hex), dtype=numpy.uint8)
            for q in queries
        ]
        qs = numpy.array(query_vectors)
        limits, similarities, I = self.faiss_index.range_search(qs, threshhold + 1)

        result = {}
        for i, query in enumerate(queries):
            match_tuples = []
            matches = [idx.item() for idx in I[limits[i] : limits[i + 1]]]
            distances = [idx for idx in similarities[limits[i] : limits[i + 1]]]
            for match, distance in zip(matches, distances):
                video_id, vpdq_match = self.idx_to_vpdq[match]
                match_tuples.append(
                    (
                        match,
                        video_id,
                        vpdq_match.frame_number,
                        vpdq_match.hex,
                        vpdq_match.quality,
                        vpdq_match.timestamp,
                        distance,
                    )
                )
            result[query.hex] = match_tuples
        return result
