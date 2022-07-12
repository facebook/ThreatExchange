import vpdq  # type: ignore
import typing as t
import binascii
import numpy  # type: ignore
from .vpdq_util import dedupe, quality_filter, TARGET_MATCH_PERCENT, QUERY_MATCH_PERCENT
from collections import namedtuple  # type: ignore

BITS_IN_VPDQ = 256
VPDQMatchTuple = "VPDQMatchTuple"


def match_VPDQ_in_another(
    hash1: t.List[vpdq.VpdqFeature],
    hash2: t.List[vpdq.VpdqFeature],
    distance_tolerance: int,
) -> int:
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
    target_hash: t.List[vpdq.VpdqFeature],
    query_hash: t.List[vpdq.VpdqFeature],
    quality_tolerance: int,
    distance_tolerance: int,
) -> t.NamedTuple:
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
    MatchResult = namedtuple(VPDQMatchTuple, [TARGET_MATCH_PERCENT, QUERY_MATCH_PERCENT])  # type: ignore
    res = MatchResult(
        target_match_cnt * 100 / len(filtered_target),
        query_match_cnt * 100 / len(filtered_query),
    )  # type: ignore
    return res
