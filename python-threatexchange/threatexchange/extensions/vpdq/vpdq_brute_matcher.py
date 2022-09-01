# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import vpdq

import typing as t

from threatexchange.signal_type.pdq.pdq_utils import simple_distance
from .vpdq_util import VpdqCompactFeature, dedupe, quality_filter, VPDQMatchResult


def match_VPDQ_in_another(
    hash1: t.List[VpdqCompactFeature],
    hash2: t.List[VpdqCompactFeature],
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
    return sum(
        any(
            simple_distance(h1.pdq_hex, h2.pdq_hex) <= distance_tolerance
            for h2 in hash2
        )
        for h1 in hash1
    )


def match_VPDQ_hash_brute(
    query_hash: t.List[VpdqCompactFeature],
    compared_hash: t.List[VpdqCompactFeature],
    quality_tolerance: int,
    distance_tolerance: int,
) -> VPDQMatchResult:
    """Match two VPDQ hashes. Return the query-match percentage and comparison-match percentage

    Args:
        query_hash : Query VPDQ hash
        compared_hash : VPDQ hash compared with query_hash
        quality_tolerance : The quality tolerance of matching two frames.
        If either frames is below this quality level then they will not be compared
        distance_tolerance : The hamming distance tolerance of between two frames.
        If the hamming distance is bigger than the tolerance, it will be considered as unmatched

    Returns:
        float: Percentage matched in total query hash
        float: Percentage matched in total comapred hash

    """
    query_match_cnt = 0
    compared_match_cnt = 0
    filtered_query = quality_filter(dedupe(query_hash), quality_tolerance)
    filtered_compared = quality_filter(dedupe(compared_hash), quality_tolerance)
    query_match_cnt = match_VPDQ_in_another(
        filtered_query, filtered_compared, distance_tolerance
    )
    compared_match_cnt = match_VPDQ_in_another(
        filtered_compared, filtered_query, distance_tolerance
    )
    return VPDQMatchResult(
        query_match_cnt * 100 / len(filtered_query),
        compared_match_cnt * 100 / len(filtered_compared),
    )
