import pytest
import io
import faiss
from threatexchange.signal_type.pdq.pdq_index2 import (
    PDQIndex2,
    _PDQHashIndex,
    DIMENSIONALITY,
    DEFAULT_MATCH_DIST,
)


@pytest.fixture
def empty_index():
    """Fixture for an empty index."""
    return PDQIndex2[str]()


@pytest.fixture
def custom_index_with_threshold():
    """Fixture for an index with custom index and threshold."""
    custom_index = faiss.IndexFlatL2(DIMENSIONALITY + 1)
    custom_threshold = DEFAULT_MATCH_DIST + 1
    return PDQIndex2[str](index=custom_index, threshold=custom_threshold)


@pytest.fixture
def sample_index():
    """Fixture for an index with a small sample set."""
    pdq_hashes = [
        "f8f8f0cee0f4a84f06370a22038f63f0b36e2ed596621e1d33e6b39c4e9c9b22",
        "f" * 64,
        "0" * 64,
        "a" * 64,
    ]
    index = PDQIndex2[str](entries=[(h, pdq_hashes.index(h)) for h in pdq_hashes])
    return index, pdq_hashes


@pytest.fixture
def sample_index_with_one_entry():
    """Fixture for an index with a small sample set."""
    pdq_hashes = [
        "f8f8f0cee0f4a84f06370a22038f63f0b36e2ed596621e1d33e6b39c4e9c9b22",
        "f" * 64,
        "0" * 64,
        "a" * 64,
    ]
    index = PDQIndex2[str](
        entries=[
            ("f8f8f0cee0f4a84f06370a22038f63f0b36e2ed596621e1d33e6b39c4e9c9b22", 0)
        ]
    )
    return index, pdq_hashes


def test_init(empty_index) -> None:
    assert empty_index.threshold == DEFAULT_MATCH_DIST
    assert isinstance(empty_index.index, _PDQHashIndex)
    assert isinstance(empty_index.index.faiss_index, faiss.IndexFlatL2)
    assert empty_index.index.faiss_index.d == DIMENSIONALITY
    assert empty_index._deduper == dict()
    assert empty_index._idx_to_entries == []


def test_serialize_deserialize(empty_index) -> None:
    buffer = io.BytesIO()
    empty_index.serialize(buffer)
    buffer.seek(0)
    deserialized_index: PDQIndex2[str] = PDQIndex2.deserialize(buffer)

    assert isinstance(deserialized_index, PDQIndex2)
    assert deserialized_index.threshold == empty_index.threshold
    assert isinstance(deserialized_index.index, _PDQHashIndex)
    assert isinstance(deserialized_index.index.faiss_index, faiss.IndexFlatL2)
    assert deserialized_index.index.faiss_index.d == DIMENSIONALITY
    assert deserialized_index._deduper == empty_index._deduper
    assert deserialized_index._idx_to_entries == empty_index._idx_to_entries


def test_serialize_deserialize_with_custom_index_threshold(
    custom_index_with_threshold,
) -> None:
    buffer = io.BytesIO()
    custom_index_with_threshold.serialize(buffer)
    buffer.seek(0)
    deserialized_index: PDQIndex2[str] = PDQIndex2.deserialize(buffer)

    assert isinstance(deserialized_index, PDQIndex2)
    assert deserialized_index.threshold == custom_index_with_threshold.threshold
    assert isinstance(deserialized_index.index, _PDQHashIndex)
    assert isinstance(deserialized_index.index.faiss_index, faiss.IndexFlatL2)
    assert deserialized_index.index.faiss_index.d == DIMENSIONALITY + 1
    assert deserialized_index._deduper == custom_index_with_threshold._deduper
    assert (
        deserialized_index._idx_to_entries
        == custom_index_with_threshold._idx_to_entries
    )


def test_empty_index_query(empty_index):
    """Test querying an empty index."""
    query_hash = "f8f8f0cee0f4a84f06370a22038f63f0b36e2ed596621e1d33e6b39c4e9c9b22"

    # Query should return empty list
    results = empty_index.query(query_hash)
    assert len(results) == 0


def test_sample_set_exact_match(sample_index):
    """Test exact matches in sample set."""
    index, pdq_hashes = sample_index

    # Query with existing hash
    query_hash = pdq_hashes[0]
    results = index.query(query_hash)

    assert len(results) == 1
    assert (
        results[0].similarity_info.distance == 0
    )  # Exact match should have distance 0


def test_sample_set_no_match(sample_index):
    """Test no matches in sample set."""
    index, _ = sample_index
    results = index.query("b" * 64)
    assert len(results) == 0


def test_sample_set_near_match(sample_index):
    """Test near matches in sample set."""
    index, pdq_hashes = sample_index

    # Create a near-match by flipping a few bits
    base_hash = pdq_hashes[0]
    near_hash = hex(int(base_hash, 16) ^ 0xF)[2:].zfill(64)  # Flip 4 bits

    results = index.query(near_hash)
    assert len(results) > 0  # Should find near matches
    assert results[0].similarity_info.distance > 0


def test_sample_set_threshold(sample_index):
    """Test distance threshold behavior."""
    _, pdq_hashes = sample_index

    narrow_index = PDQIndex2[str](threshold=10)  # Strict matching
    wide_index = PDQIndex2[str](threshold=50)  # Loose matching

    for hash_str in pdq_hashes:
        narrow_index.add(hash_str, hash_str)
        wide_index.add(hash_str, hash_str)

    # Create a test hash with known distance
    base_hash = pdq_hashes[0]
    test_hash = hex(int(base_hash, 16) ^ ((1 << 20) - 1))[2:].zfill(
        64
    )  # ~20 bits different

    narrow_results = narrow_index.query(test_hash)
    wide_results = wide_index.query(test_hash)

    assert len(wide_results) > len(narrow_results)  # Wide threshold should match more


def test_duplicate_handling(sample_index):
    """Test how the index handles duplicate entries."""
    index, pdq_hashes = sample_index

    # Add same hash multiple times
    test_hash = pdq_hashes[0]
    index.add_all(entries=[(test_hash, i) for i in range(3)])

    results = index.query(test_hash)

    # Should find all entries associated with the hash
    assert len(results) == 4
    for result in results:
        assert result.similarity_info.distance == 0


def test_one_entry_sample_index(sample_index_with_one_entry):
    """Test how the index handles when it only has one entry."""
    index, pdq_hashes = sample_index_with_one_entry

    matching_test_hash = pdq_hashes[0]  # This is the existing hash in index
    unmatching_test_hash = pdq_hashes[1]

    results = index.query(matching_test_hash)
    # Should find 1 entry associated with the hash
    assert len(results) == 1
    assert results[0].similarity_info.distance == 0

    results = index.query(unmatching_test_hash)
    assert len(results) == 0
