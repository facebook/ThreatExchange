# Copyright (c) Meta Platforms, Inc. and affiliates.

import io
import random
import typing as t

import faiss

from threatexchange.signal_type.pdq.pdq_index2 import PDQIndex2
from threatexchange.signal_type.pdq.pdq_utils import simple_distance
from threatexchange.signal_type.pdq.signal import PdqSignal


def _get_hash_generator(seed: int = 42):
    random.seed(seed)

    def get_n_hashes(n: int):
        return [PdqSignal.get_random_signal() for _ in range(n)]

    return get_n_hashes


def _brute_force_match(
    base: t.List[str], query: str, threshold: int = 32
) -> t.Set[t.Tuple[int, int]]:
    matches = set()

    for i, base_hash in enumerate(base):
        distance = simple_distance(base_hash, query)
        if distance <= threshold:
            matches.add((i, distance))
    return matches


def _generate_random_hash_with_distance(hash: str, distance: int) -> str:
    if not (0 <= distance <= 256):
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
    get_random_hashes = _get_hash_generator()
    base_hashes = get_random_hashes(100)
    # Make sure base_hashes and query_hashes have at least 10 similar hashes
    query_hashes = base_hashes[:10] + get_random_hashes(1000)

    brute_force_matches = {
        query_hash: _brute_force_match(base_hashes, query_hash)
        for query_hash in query_hashes
    }

    index = PDQIndex2(entries=[(h, base_hashes.index(h)) for h in base_hashes])

    for query_hash in query_hashes:
        expected_indices = brute_force_matches[query_hash]
        index_results = index.query(query_hash)

        result_indices: t.Set[t.Tuple[t.Any, int]] = {
            (result.metadata, result.similarity_info.distance)
            for result in index_results
        }

        assert result_indices == expected_indices, (
            f"Mismatch for hash {query_hash}: "
            f"Expected {expected_indices}, Got {result_indices}"
        )


def test_pdq_index_with_exact_distance():
    get_random_hashes = _get_hash_generator()
    base_hashes = get_random_hashes(100)

    thresholds: t.List[int] = [10, 31, 50]

    indexes = [
        PDQIndex2(
            entries=[(h, base_hashes.index(h)) for h in base_hashes],
            threshold=thres,
        )
        for thres in thresholds
    ]

    distances: t.List[int] = [0, 1, 20, 30, 31, 60]
    query_hash = base_hashes[0]

    for i in range(len(indexes)):
        index = indexes[i]

        for dist in distances:
            query_hash_w_dist = _generate_random_hash_with_distance(query_hash, dist)
            results = index.query(query_hash_w_dist)
            result_indices = {result.similarity_info.distance for result in results}
            if dist <= thresholds[i]:
                assert dist in result_indices


def test_serialize_deserialize_index():
    get_random_hashes = _get_hash_generator()
    base_hashes = get_random_hashes(100)
    index: PDQIndex2 = PDQIndex2(
        entries=[(h, base_hashes.index(h)) for h in base_hashes]
    )

    buffer = io.BytesIO()
    index.serialize(buffer)
    buffer.seek(0)
    deserialized_index: PDQIndex2 = PDQIndex2.deserialize(buffer)

    assert isinstance(deserialized_index, PDQIndex2)
    assert isinstance(deserialized_index._index.faiss_index, faiss.IndexFlatL2)
    assert deserialized_index.threshold == index.threshold
    assert deserialized_index._deduper == index._deduper
    assert deserialized_index._idx_to_entries == index._idx_to_entries


def test_empty_index_query():
    """Test querying an empty index."""
    index: PDQIndex2 = PDQIndex2()

    # Query should return empty list
    results = index.query(PdqSignal.get_random_signal())
    assert len(results) == 0


def test_sample_set_no_match():
    """Test no matches in sample set."""
    get_random_hashes = _get_hash_generator()
    base_hashes = get_random_hashes(100)
    index = PDQIndex2(entries=[(h, base_hashes.index(h)) for h in base_hashes])
    results = index.query("b" * 64)
    assert len(results) == 0


def test_duplicate_handling():
    """Test how the index handles duplicate entries."""
    get_random_hashes = _get_hash_generator()
    base_hashes = get_random_hashes(100)
    index = PDQIndex2(entries=[(h, base_hashes.index(h)) for h in base_hashes])

    # Add same hash multiple times
    index.add_all(entries=[(base_hashes[0], i) for i in range(3)])

    results = index.query(base_hashes[0])

    # Should find all entries associated with the hash
    assert len(results) == 4
    for result in results:
        assert result.similarity_info.distance == 0


def test_one_entry_sample_index():
    """
    Test how the index handles when it only has one entry.

    See issue github.com/facebook/ThreatExchange/issues/1318
    """
    get_random_hashes = _get_hash_generator()
    base_hashes = get_random_hashes(100)
    index = PDQIndex2(entries=[(base_hashes[0], 0)])

    matching_test_hash = base_hashes[0]  # This is the existing hash in index
    unmatching_test_hash = base_hashes[1]

    results = index.query(matching_test_hash)
    # Should find 1 entry associated with the hash
    assert len(results) == 1
    assert results[0].similarity_info.distance == 0

    results = index.query(unmatching_test_hash)
    assert len(results) == 0


def test_reset_index(index):
    # FIXME: There problem needs to be a test case here, though I can't get one working
    pass
