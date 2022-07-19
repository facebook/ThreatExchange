# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import vpdq
import faiss
from .vpdq_util import dedupe, quality_filter
from threatexchange.extensions.video_vpdq.vpdq_util import VPDQMatchResult
import typing as t
import numpy
import binascii

BITS_IN_VPDQ = 256
VPDQ_VIDEOID_TYPE = t.Union[str, int]


class VPDQFlatHashIndex:
    """Wrapper around an faiss binary index for use with searching for similar VPDQ features

    The "flat" variant uses an exhaustive search approach that may use less memory than other approaches and may be more
    performant when using larger thresholds for VPDQ similarity.
    """

    def __init__(self) -> None:
        faiss_index = faiss.IndexBinaryFlat(BITS_IN_VPDQ)
        self.faiss_index = faiss_index
        self.idx_to_vpdq: t.List[t.Tuple[VPDQ_VIDEOID_TYPE, vpdq.VpdqFeature]] = []
        self.video_id_to_vpdq: t.Dict[VPDQ_VIDEOID_TYPE, t.List[vpdq.VpdqFeature]] = {}
        super().__init__()

    def get_video_frame_counts(
        self, video_id: VPDQ_VIDEOID_TYPE, quality_tolerance: int
    ) -> int:
        """
        Args:
            video_id : Unique video id correspondes to video
            quality_tolerance : The quality tolerance of frames.
            If frame is below this quality level then they will not be counted
        Returns:
            Size of VPDQ features in the video that has a quality larger or equal to quality_tolerance
        """
        return len(quality_filter(self.video_id_to_vpdq[video_id], quality_tolerance))

    def add_single_video(
        self,
        hashes: t.List[vpdq.VpdqFeature],
        video_id: VPDQ_VIDEOID_TYPE,
    ) -> None:
        """
        Args:
            hashes : One video's VPDQ features of to create the index with
            video_id : Unique video id correspondes to video
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

    def search_with_raw_features_in_result(
        self,
        queries: t.List[vpdq.VpdqFeature],
        threshhold: int,
    ) -> t.Dict[str, t.List]:
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

    def search_with_match_percentage_in_result(
        self,
        query_hash: t.List[vpdq.VpdqFeature],
        quality_tolerance: int,
        distance_tolerance: int,
    ) -> t.List[t.Tuple[VPDQ_VIDEOID_TYPE, VPDQMatchResult]]:
        """Searches this VPDQ index for target hashes within the index that are no more than the threshold away from the query hashes by
            hamming distance.

        Args:
            query_hash : Query VPDQ hash
            VPDQ_index : VPDQ index to be searched for query hash
            quality_tolerance (int): The quality tolerance of matching two frames.
            If either frames is below this quality level then they will not be compared
            distance_tolerance (int): The hamming distance tolerance of between two frames.
            If the hamming distance is bigger than the tolerance, it will be considered as unmatched

        Returns:
            VPDQ Video id corresponds with its VPDQMatchResult
        """
        query_hash = quality_filter(dedupe(query_hash), quality_tolerance)
        ret = self.search_with_raw_features_in_result(query_hash, distance_tolerance)
        query_matched: t.Dict[VPDQ_VIDEOID_TYPE, t.Set] = {}
        index_matched: t.Dict[VPDQ_VIDEOID_TYPE, t.Set] = {}
        for r in ret:
            for matched_frame in ret[r]:
                # query_str =>  (id, video_id, frame_number, hex_str of hash, quality, timestamp, distance)
                _, video_id, frame_number, _, quality, _, _ = matched_frame
                if quality < quality_tolerance:
                    continue

                if video_id not in query_matched:
                    query_matched[video_id] = set()
                query_matched[video_id].add(r)

                if video_id not in index_matched:
                    index_matched[video_id] = set()
                index_matched[video_id].add(frame_number)

        return [
            (
                video_id,
                VPDQMatchResult(
                    len(query_matched[video_id]) * 100 / len(query_hash),
                    len(index_matched[video_id])
                    * 100
                    / self.get_video_frame_counts(video_id, quality_tolerance),
                ),
            )
            for video_id in sorted(query_matched)
        ]
