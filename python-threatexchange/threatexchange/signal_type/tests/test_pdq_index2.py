import typing as t
import numpy as np
import random

from threatexchange.signal_type.pdq.pdq_index2 import PDQIndex2
from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.pdq.pdq_utils import convert_pdq_strings_to_ndarray

SAMPLE_HASHES = [PdqSignal.get_random_signal() for _ in range(100)]


def _brute_force_match(
    base: t.List[str], query: str, threshold: int = 32
) -> t.Set[int]:
    matches = set()
    query_arr = convert_pdq_strings_to_ndarray([query])[0]

    for i, base_hash in enumerate(base):
        base_arr = convert_pdq_strings_to_ndarray([base_hash])[0]
        distance = np.count_nonzero(query_arr != base_arr)
        if distance <= threshold:
            matches.add(i)
    return matches


def _generate_random_hash_with_distance(hash: str, distance: int) -> str:
    if len(hash) != 64 or not all(c in "0123456789abcdef" for c in hash.lower()):
        raise ValueError("Hash must be a 64-character hexadecimal string")
    if distance < 0 or distance > 256:
        raise ValueError("Distance must be between 0 and 256")

    hash_bits = bin(int(hash, 16))[2:].zfill(256)  # Convert hash to binary
    bits = list(hash_bits)
    positions = random.sample(
        range(256), distance
    )  # Randomly select unique positions to flip
    for pos in positions:
        bits[pos] = "0" if bits[pos] == "1" else "1"  # Flip selected bit positions
    modified_hash = hex(int("".join(bits), 2))[2:].zfill(64)  # Convert back to hex

    return modified_hash


def test_pdq_index():
    # Make sure base_hashes and query_hashes have at least 100 similar hashes
    base_hashes = SAMPLE_HASHES + [PdqSignal.get_random_signal() for _ in range(1000)]
    query_hashes = SAMPLE_HASHES + [PdqSignal.get_random_signal() for _ in range(10000)]

    brute_force_matches = {
        query_hash: _brute_force_match(base_hashes, query_hash)
        for query_hash in query_hashes
    }

    index = PDQIndex2()
    for i, base_hash in enumerate(base_hashes):
        index.add(base_hash, i)

    for query_hash in query_hashes:
        expected_indices = brute_force_matches[query_hash]
        index_results = index.query(query_hash)

        result_indices = {result.metadata for result in index_results}

        assert result_indices == expected_indices, (
            f"Mismatch for hash {query_hash}: "
            f"Expected {expected_indices}, Got {result_indices}"
        )


def test_pdq_index_with_exact_distance():
    thresholds: t.List[int] = [10, 31, 50]
    indexes: t.List[PDQIndex2] = []
    for thres in thresholds:
        index = PDQIndex2(
            entries=[(h, SAMPLE_HASHES.index(h)) for h in SAMPLE_HASHES],
            threshold=thres,
        )
        indexes.append(index)

    distances: t.List[int] = [0, 1, 20, 30, 31, 60]
    query_hash = SAMPLE_HASHES[0]

    for i in range(len(indexes)):
        index = indexes[i]

        for dist in distances:
            query_hash_w_dist = _generate_random_hash_with_distance(query_hash, dist)
            results = index.query(query_hash_w_dist)
            result_indices = {result.similarity_info.distance for result in results}
            if dist <= thresholds[i]:
                assert dist in result_indices


def test_empty_index_query():
    """Test querying an empty index."""
    index = PDQIndex2()

    # Query should return empty list
    results = index.query(PdqSignal.get_random_signal())
    assert len(results) == 0


def test_sample_set_no_match():
    """Test no matches in sample set."""
    index = PDQIndex2(entries=[(h, SAMPLE_HASHES.index(h)) for h in SAMPLE_HASHES])
    results = index.query("b" * 64)
    assert len(results) == 0


def test_duplicate_handling():
    """Test how the index handles duplicate entries."""
    index = PDQIndex2(entries=[(h, SAMPLE_HASHES.index(h)) for h in SAMPLE_HASHES])

    # Add same hash multiple times
    index.add_all(entries=[(SAMPLE_HASHES[0], i) for i in range(3)])

    results = index.query(SAMPLE_HASHES[0])

    # Should find all entries associated with the hash
    assert len(results) == 4
    for result in results:
        assert result.similarity_info.distance == 0


def test_one_entry_sample_index():
    """Test how the index handles when it only has one entry."""
    index = PDQIndex2(entries=[(SAMPLE_HASHES[0], 0)])

    matching_test_hash = SAMPLE_HASHES[0]  # This is the existing hash in index
    unmatching_test_hash = SAMPLE_HASHES[1]

    results = index.query(matching_test_hash)
    # Should find 1 entry associated with the hash
    assert len(results) == 1
    assert results[0].similarity_info.distance == 0

    results = index.query(unmatching_test_hash)
    assert len(results) == 0
