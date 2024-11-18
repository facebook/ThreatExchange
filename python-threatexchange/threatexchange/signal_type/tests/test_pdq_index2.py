import pytest
import io
import faiss
from threatexchange.signal_type.pdq.pdq_index2 import PDQIndex2, _PDQFaissIndex
from threatexchange.signal_type.pdq.signal import PDQ_CONFIDENT_MATCH_THRESHOLD
from threatexchange.signal_type.pdq.pdq_utils import BITS_IN_PDQ

SAMPLE_HASH = "f8f8f0cee0f4a84f06370a22038f63f0b36e2ed596621e1d33e6b39c4e9c9b22"

SAMPLE_HASHES = [
    SAMPLE_HASH,
    "f" * 64,
    "0" * 64,
    "a" * 64,
]


def test_empty_index_query():
    """Test querying an empty index."""
    index = PDQIndex2()

    # Query should return empty list
    results = index.query(SAMPLE_HASH)
    assert len(results) == 0


def test_sample_set_exact_match():
    """Test exact matches in sample set."""
    index = PDQIndex2(entries=[(h, SAMPLE_HASHES.index(h)) for h in SAMPLE_HASHES])

    # Query with existing hash
    results = index.query(SAMPLE_HASH)

    assert len(results) == 1
    assert (
        results[0].similarity_info.distance == 0
    )  # Exact match should have distance 0


def test_sample_set_no_match():
    """Test no matches in sample set."""
    index = PDQIndex2(entries=[(h, SAMPLE_HASHES.index(h)) for h in SAMPLE_HASHES])
    results = index.query("b" * 64)
    assert len(results) == 0


def test_sample_set_near_match():
    """Test near matches in sample set."""
    index = PDQIndex2(entries=[(h, SAMPLE_HASHES.index(h)) for h in SAMPLE_HASHES])
    # Create a near-match by flipping a few bits
    near_hash = hex(int(SAMPLE_HASH, 16) ^ 0xF)[2:].zfill(64)

    results = index.query(near_hash)
    assert len(results) > 0  # Should find near matches
    assert results[0].similarity_info.distance > 0


def test_sample_set_threshold():
    """Verify that the sample set respects the specified distance threshold."""
    narrow_index = PDQIndex2[str](threshold=10)  # Strict matching
    wide_index = PDQIndex2[str](threshold=50)  # Loose matching

    for hash_str in SAMPLE_HASHES:
        narrow_index.add(hash_str, hash_str)
        wide_index.add(hash_str, hash_str)

    # Create a test hash with known distance
    test_hash = hex(int(SAMPLE_HASH, 16) ^ ((1 << 20) - 1))[2:].zfill(
        64
    )  # ~20 bits different

    narrow_results = narrow_index.query(test_hash)
    wide_results = wide_index.query(test_hash)

    assert len(wide_results) > len(narrow_results)  # Wide threshold should match more


def test_duplicate_handling():
    """Test how the index handles duplicate entries."""
    index = PDQIndex2(entries=[(h, SAMPLE_HASHES.index(h)) for h in SAMPLE_HASHES])

    # Add same hash multiple times
    index.add_all(entries=[(SAMPLE_HASH, i) for i in range(3)])

    results = index.query(SAMPLE_HASH)

    # Should find all entries associated with the hash
    assert len(results) == 4
    for result in results:
        assert result.similarity_info.distance == 0


def test_one_entry_sample_index():
    """Test how the index handles when it only has one entry."""
    index = PDQIndex2(entries=[(SAMPLE_HASH, 0)])

    matching_test_hash = SAMPLE_HASHES[0]  # This is the existing hash in index
    unmatching_test_hash = SAMPLE_HASHES[1]

    results = index.query(matching_test_hash)
    # Should find 1 entry associated with the hash
    assert len(results) == 1
    assert results[0].similarity_info.distance == 0

    results = index.query(unmatching_test_hash)
    assert len(results) == 0
