import pytest
import io
import faiss
from threatexchange.signal_type.index2 import (
    SignalTypeIndex2,
    _PDQHashIndex,
    DIMENSIONALITY,
    DEFAULT_MATCH_DIST,
)


@pytest.fixture
def empty_index():
    """Fixture for an empty index."""
    return SignalTypeIndex2[str]()


@pytest.fixture
def custom_index_with_threshold():
    """Fixture for an index with custom index and threshold."""
    custom_index = faiss.IndexFlatL2(DIMENSIONALITY + 1)
    custom_threshold = DEFAULT_MATCH_DIST + 1
    return SignalTypeIndex2[str](faiss_index=custom_index, threshold=custom_threshold)


@pytest.fixture
def sample_index():
    """Fixture for an index with a small sample set."""
    index = SignalTypeIndex2[str]()
    pdq_hashes = [
        "f" * 64,  # All f's
        "0" * 64,  # All 0's
        "a" * 64,  # All a's
        "f8f8f0cee0f4a84f06370a22038f63f0b36e2ed596621e1d33e6b39c4e9c9b22",  # Sample hash
    ]
    return index, pdq_hashes


def test_init(empty_index) -> None:
    assert empty_index.threshold == DEFAULT_MATCH_DIST
    assert isinstance(empty_index.faiss_index, _PDQHashIndex)
    assert isinstance(empty_index.faiss_index.faiss_index, faiss.IndexFlatL2)
    assert empty_index.faiss_index.faiss_index.d == DIMENSIONALITY
    assert empty_index._deduper == set()
    assert empty_index._entries == []


def test_serialize_deserialize(empty_index) -> None:
    buffer = io.BytesIO()
    empty_index.serialize(buffer)
    buffer.seek(0)
    deserialized_index: SignalTypeIndex2[str] = SignalTypeIndex2.deserialize(buffer)

    assert isinstance(deserialized_index, SignalTypeIndex2)
    assert deserialized_index.threshold == empty_index.threshold
    assert isinstance(deserialized_index.faiss_index, _PDQHashIndex)
    assert isinstance(deserialized_index.faiss_index.faiss_index, faiss.IndexFlatL2)
    assert deserialized_index.faiss_index.faiss_index.d == DIMENSIONALITY
    assert deserialized_index._deduper == empty_index._deduper
    assert deserialized_index._entries == empty_index._entries


def test_serialize_deserialize_with_custom_index_threshold(
    custom_index_with_threshold,
) -> None:
    buffer = io.BytesIO()
    custom_index_with_threshold.serialize(buffer)
    buffer.seek(0)
    deserialized_index: SignalTypeIndex2[int] = SignalTypeIndex2.deserialize(buffer)

    assert isinstance(deserialized_index, SignalTypeIndex2)
    assert deserialized_index.threshold == custom_index_with_threshold.threshold
    assert isinstance(deserialized_index.faiss_index, _PDQHashIndex)
    assert isinstance(deserialized_index.faiss_index.faiss_index, faiss.IndexFlatL2)
    assert deserialized_index.faiss_index.faiss_index.d == DIMENSIONALITY + 1
    assert deserialized_index._deduper == custom_index_with_threshold._deduper
    assert deserialized_index._entries == custom_index_with_threshold._entries


def test_empty_index_query(empty_index):
    """Test querying an empty index."""
    query_hash = "f8f8f0cee0f4a84f06370a22038f63f0b36e2ed596621e1d33e6b39c4e9c9b22"

    # Query should return empty list
    results = empty_index.query(query=query_hash)
    assert len(results) == 0


def test_sample_set_exact_match(sample_index):
    """Test exact matches in sample set."""
    index, pdq_hashes = sample_index

    # Add hashes to index
    for hash_str in pdq_hashes:
        index.add(hash_str, hash_str)  # Using hash as its own identifier

    # Query with existing hash
    query_hash = pdq_hashes[0]
    results = index.query(query_hash)

    assert len(results) == 1
    assert (
        results[0].similarity_info.distance == 0
    )  # Exact match should have distance 0


def test_sample_set_near_match(sample_index):
    """Test near matches in sample set."""
    index, pdq_hashes = sample_index

    # Add hashes to index
    for hash_str in pdq_hashes:
        index.add(hash_str, hash_str)  # Using hash as its own identifier

    # Create a near-match by flipping a few bits
    base_hash = pdq_hashes[0]
    near_hash = hex(int(base_hash, 16) ^ 0xF)[2:].zfill(64)  # Flip 4 bits

    results = index.query(near_hash)
    assert len(results) > 0  # Should find near matches
    assert results[0].similarity_info.distance > 0


def test_sample_set_threshold(sample_index):
    """Test distance threshold behavior."""
    _, pdq_hashes = sample_index

    narrow_index = SignalTypeIndex2[str](threshold=10)  # Strict matching
    wide_index = SignalTypeIndex2[str](threshold=50)  # Loose matching

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
    for i in range(3):
        index.add(test_hash, f"entry_{i}")

    results = index.query(test_hash)

    # Should find all entries associated with the hash
    assert len(results) == 3
