import vpdq
import typing as t
import faiss  # type: ignore
import binascii
import numpy  # type: ignore

BITS_IN_VPDQ = 256


def dedupe(hashes):
    """Filter out the VPDQ feature with exact same hash in a list of VPDQ features

    Args:
        hashes (list of VPDQ feature)

    Returns:
        list of VPDQ feature: List of VPDQeatures with unique hashes
    """
    unique_hashes = set()
    ret = []
    for h in hashes:
        if h.hex not in unique_hashes:
            ret.append(h)
            unique_hashes.add(h.hex)
    return ret


def quality_filter(hashes, quality_tolerance):
    """Filter VPDQ feature that has a quality lower than quality_tolerance

    Args:
        hashes (list of VPDQ feature)
        distance_tolerance (int): If frames is this quality level then it will be ignored

    Returns:
        list of VPDQ feature: List of VPDQeatures with quality higher than distance_tolerance
    """
    return list(filter(lambda hash: hash.quality >= quality_tolerance, hashes))


def match_VPDQ_in_another(hash1, hash2, distance_tolerance):
    """Count matches of hash1 in hash2

    Args:
        hash1 (list of VPDQ feature)
        hash2 (list of VPDQ feature)
        distance_tolerance (int):The hamming distance tolerance of between two frames.
        If the hamming distance is bigger than the tolerance, it will be considered as unmatched

    Returns:
        int: The count of matches of hash1 in hash2
    """
    cnt = 0
    for h1 in hash1:
        for h2 in hash2:
            if h1.hamming_distance(h2) < distance_tolerance:
                cnt += 1
                break
    return cnt


def match_VPDQ_hash_brute(
    target_hash, query_hash, quality_tolerance, distance_tolerance
):
    """Match two VPDQ hashes. Return the query-match percentage and target-match percentage

    Args:
        target_hash (list of VPDQ feature): Target VPDQ hash
        query_hash (list of VPDQ feature): Query VPDQ hash
        quality_tolerance (int): The quality tolerance of matching two frames.
        If either frames is below this quality level then they will not be compared
        distance_tolerance (int): The hamming distance tolerance of between two frames.
        If the hamming distance is bigger than the tolerance, it will be considered as unmatched

    Returns:
        float: Percentage matched in total target hash
        flaot: Percentage matched in total query hash

    """
    target_match_cnt = 0
    query_match_cnt = 0
    filtered_target = quality_filter(dedupe(target_hash), quality_tolerance)
    filtered_query = quality_filter(dedupe(query_hash), quality_tolerance)
    target_match_cnt = match_VPDQ_in_another(
        filtered_target, filtered_query, distance_tolerance
    )
    query_match_cnt = match_VPDQ_in_another(
        filtered_query, filtered_target, distance_tolerance
    )
    return target_match_cnt * 100 / len(filtered_target), query_match_cnt * 100 / len(
        filtered_query
    )


# TODO: Add quality Filter
def match_VPDQ_FAISS(target_hash, VPDQ_index, quality_tolerance, distance_tolerance):
    """Searches this VPDQ index for target hashes within the index that are no more than the threshold away from the query hashes by
        hamming distance.

    Args:
        target_hash (list of VPDQfeature): Target VPDQ hash
        VPDQ_index (VPDQFlatHashIndex): Query VPDQ hash
        quality_tolerance (int): The quality tolerance of matching two frames.
        If either frames is below this quality level then they will not be compared
        distance_tolerance (int): The hamming distance tolerance of between two frames.
        If the hamming distance is bigger than the tolerance, it will be considered as unmatched

    Returns:
        float: Percentage matched in total target hash
        flaot: Percentage matched in total query hash
    """
    target_hash = quality_filter(dedupe(target_hash), quality_tolerance)
    ret = VPDQ_index.search_with_detail_in_result(target_hash, 31)
    target_matched = {}
    index_matched = {}
    for r in ret:
        for matched_frame in ret[r]:
            # query_str =>  (id, video_id, frame_number, hex_str of hash, quality, distance)
            _, video_id, frame_number, _, quality, _ = matched_frame
            if quality < quality_tolerance:
                continue

            if video_id not in target_matched:
                target_matched[video_id] = set()
            target_matched[video_id].add(r)

            if video_id not in index_matched:
                index_matched[video_id] = set()
            index_matched[video_id].add(frame_number)

    return [
        (
            video_id,
            len(target_matched[video_id]) * 100 / len(target_hash),
            len(index_matched[video_id])
            * 100
            / VPDQ_index.get_video_frame_counts(video_id, quality_tolerance),
        )
        for video_id in sorted(target_matched)
    ]


class VPDQFlatHashIndex:
    """Wrapper around an faiss binary index for use with searching for similar VPDQ features

    The "flat" variant uses an exhaustive search approach that may use less memory than other approaches and may be more
    performant when using larger thresholds for VPDQ similarity.
    """

    def __init__(self) -> None:
        faiss_index = faiss.IndexBinaryFlat(BITS_IN_VPDQ)
        self.faiss_index = faiss_index
        self._idx_to_vpdq = []
        self._video_id_to_vpdq = {}
        super().__init__()

    def get_video_frame_counts(self, video_id: int, quality_tolerance: int):
        """
        Args:
            video_id (int)
            quality_tolerance (int)
        Returns:
            Size of VPDQ features in the video that has a quality larger or equal to quality_tolerance
        """
        return len(quality_filter(self._video_id_to_vpdq[video_id], quality_tolerance))

    def add_multiple_videos(
        self,
        hashes: t.Iterable[vpdq.vpdq_feature],
        video_id: t.Iterable[int],
    ):
        """
        Args:
            hashes (sequence of VPDQ feature): Multiple videos' VPDQ features to create the index with
            video_id (sequence of int): Video id for the hashes
        """
        for h, id in zip(hashes, video_id):
            self.add_single_video(h, id)

    def add_single_video(
        self,
        hashes: t.Iterable[vpdq.vpdq_feature],
        video_id: int,
    ):
        """
        Args:
            hashes (sequence of VPDQ feature): One video's VPDQ features of to create the index with
            video_id (int): Video id corresponeds to the hashes in a single video
        """
        hashes = dedupe(hashes)
        self._idx_to_vpdq.extend([(video_id, h) for h in hashes])
        self._video_id_to_vpdq[video_id] = hashes
        hex_hashes = [h.hex for h in hashes]
        hash_bytes = [binascii.unhexlify(h) for h in hex_hashes]
        vectors = list(
            map(lambda h: numpy.frombuffer(h, dtype=numpy.uint8), hash_bytes)
        )
        self.faiss_index.add(numpy.array(vectors))

    def search_with_detail_in_result(
        self,
        queries: t.Sequence[vpdq.vpdq_feature],
        threshhold: int,
    ):
        """
        Searches this index for PDQ hashes within the index that are no more than the threshold away from the query hashes by
        hamming distance.

        Args:
            queries (sequence of VPDQ feature): The VPDQ features to against the index
            threshold (int): Threshold value to use for this search. The hamming distance between the result hashes and the related query will
            be no more than the threshold value. i.e., hamming_dist(q_i,r_i_j) <= threshold.

        Returns:
        sequence of matches per query
            For each query provided in queries, the returned sequence will contain a sequence of matches within the index
            that were within threshold hamming distance of that query. These matches will be (id, video_id, frame_number,
            hex_str of hash, quality, distance). The inner sequences may be empty in the case of no hashes within the index.
            The same VPDQ feature may also appear in more than one inner sequence if it matches multiple query hashes.
            For example the hash "000000000000000000000000000000000000000000000000000000000000FFFF" would match both
            "00000000000000000000000000000000000000000000000000000000FFFFFFFF" and
            "0000000000000000000000000000000000000000000000000000000000000000" for a threshold of 16. Thus it would appear in
            the entry for both the hashes if they were both in the queries list.

            eg.
            query_str =>  (id, video_id, frame_number, hex_str of hash, quality, distance)
            result = {
                "000000000000000000000000000000000000000000000000000000000000FFFF": [
                    (12345678901, 5, 38, "00000000000000000000000000000000000000000000000000000000FFFFFFFF",97, 16.0)
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
                video_id, vpdq_match = self._idx_to_vpdq[match]
                match_tuples.append(
                    (
                        match,
                        video_id,
                        vpdq_match.frame_number,
                        vpdq_match.hex,
                        vpdq_match.quality,
                        distance,
                    )
                )
            result[query.hex] = match_tuples
        return result

    def __getstate__(self):
        data = faiss.serialize_index_binary(self.faiss_index)
        return data

    def __setstate__(self, data):
        self.faiss_index = faiss.deserialize_index_binary(data)
