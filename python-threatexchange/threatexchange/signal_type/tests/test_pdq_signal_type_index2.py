import typing as t
import random
import io
import faiss
import pytest
import pickle

from threatexchange.signal_type.pdq.pdq_index2 import PDQSignalTypeIndex2
from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.pdq.pdq_utils import (
    simple_distance,
    PDQ_CONFIDENT_MATCH_THRESHOLD,
)
from threatexchange.signal_type.pdq.pdq_index import PDQIndex

def _get_hash_generator(seed: int = 42):
    random.seed(seed)

    def get_n_hashes(n: int):
        return [PdqSignal.get_random_signal() for _ in range(n)]

    return get_n_hashes

def _brute_force_match(
    base: t.List[str], query: str, threshold: int = PDQ_CONFIDENT_MATCH_THRESHOLD
) -> t.Set[t.Tuple[int, int]]:
    matches = set()

    for i, base_hash in enumerate(base):
        distance = simple_distance(base_hash, query)
        if distance <= threshold:
            matches.add((i, distance))
    return matches

def test_flat_index_small_dataset():
    """Test that flat index is used for small datasets."""
    get_random_hashes = _get_hash_generator()
    base_hashes = get_random_hashes(100) # Below IVF threshold here. 
    index = PDQSignalTypeIndex2.build([(h, base_hashes.index(h)) for h in base_hashes])

    assert isinstance(index._index._index.faiss_index, faiss.IndexFlatL2)

def test_ivf_index_large_dataset():
    """Test that IVF index is used for large datasets."""
    get_random_hashes = _get_hash_generator()
    base_hashes = get_random_hashes(2000)  
    index = PDQSignalTypeIndex2.build([(h, base_hashes.index(h)) for h in base_hashes])

    assert isinstance(index._index._index.faiss_index, faiss.IndexIVFFlat)

def test_empty_index_query():
    """Test querying an empty index."""
    index = PDQSignalTypeIndex2()
    results = index.query(PdqSignal.get_random_signal())
    assert len(results) == 0

def test_single_hash_query():
    """Test querying with a single hash."""
    hash_str = PdqSignal.get_random_signal()
    index = PDQSignalTypeIndex2()
    index.add(hash_str, "test_entry")

    results = index.query(hash_str)
    assert len(results) == 1
    assert results[0].metadata == "test_entry"
    assert results[0].similarity_info.distance == 0

def test_add_all_and_query():
    """Test adding multiple hashes and querying."""
    get_random_hashes = _get_hash_generator()
    base_hashes = get_random_hashes(100)
    index = PDQSignalTypeIndex2()
    index.add_all([(h, base_hashes.index(h)) for h in base_hashes])

    results = index.query(base_hashes[0])
    assert len(results) >= 1  
    assert any(r.metadata == 0 for r in results)  

def test_build_and_query():
    """Test building index and querying."""
    get_random_hashes = _get_hash_generator()
    base_hashes = get_random_hashes(100)
    index = PDQSignalTypeIndex2.build([(h, base_hashes.index(h)) for h in base_hashes])

    results = index.query(base_hashes[0])
    assert len(results) >= 1  
    assert any(r.metadata == 0 for r in results)  

def test_len():
    """Test length reporting."""
    get_random_hashes = _get_hash_generator()
    base_hashes = get_random_hashes(100)
    index = PDQSignalTypeIndex2()
    assert len(index) == 0

    index.add_all([(h, base_hashes.index(h)) for h in base_hashes])
    assert len(index) == 100

def test_serialize_deserialize_empty_index():
    """Test serialization/deserialization of empty index."""
    index = PDQSignalTypeIndex2()
    buffer = io.BytesIO()

    index.serialize(buffer)
    buffer.seek(0)

    deserialized = PDQSignalTypeIndex2.deserialize(buffer)
    assert len(deserialized) == 0
    assert deserialized._index is None

def test_serialize_deserialize_flat_index():
    """Test serialization/deserialization of flat index."""
    get_random_hashes = _get_hash_generator()
    base_hashes = get_random_hashes(100)  
    index = PDQSignalTypeIndex2.build([(h, base_hashes.index(h)) for h in base_hashes])
    buffer = io.BytesIO()

    index.serialize(buffer)
    buffer.seek(0)

    deserialized = PDQSignalTypeIndex2.deserialize(buffer)
    assert len(deserialized) == len(index)
    assert isinstance(deserialized._index._index.faiss_index, faiss.IndexFlatL2)

    results = deserialized.query(base_hashes[0])
    assert len(results) >= 1
    assert any(r.metadata == 0 for r in results)

def test_serialize_deserialize_ivf_index():
    """Test serialization/deserialization of IVF index."""
    get_random_hashes = _get_hash_generator()
    base_hashes = get_random_hashes(2000)  
    index = PDQSignalTypeIndex2.build([(h, base_hashes.index(h)) for h in base_hashes])
    buffer = io.BytesIO()

    index.serialize(buffer)
    buffer.seek(0)

    deserialized = PDQSignalTypeIndex2.deserialize(buffer)
    assert len(deserialized) == len(index)
    assert isinstance(deserialized._index._index.faiss_index, faiss.IndexIVFFlat)

    results = deserialized.query(base_hashes[0])
    assert len(results) >= 1
    assert any(r.metadata == 0 for r in results)

def test_compatibility_with_old_index():
    """Test that we can read indices serialized with the old PDQIndex class."""

    get_random_hashes = _get_hash_generator()
    base_hashes = get_random_hashes(100)
    old_index = PDQIndex([(h, base_hashes.index(h)) for h in base_hashes])

    buffer = io.BytesIO()
    pickle.dump(old_index, buffer)
    buffer.seek(0)

    loaded_old_index = pickle.load(buffer)

    query_hash = base_hashes[0]
    old_results = loaded_old_index.query(query_hash)

    new_index = PDQSignalTypeIndex2.build(
        [(h, base_hashes.index(h)) for h in base_hashes]
    )
    new_results = new_index.query(query_hash)

    assert len(old_results) >= 1
    assert len(new_results) >= 1
    assert any(r.metadata == 0 for r in old_results)
    assert any(r.metadata == 0 for r in new_results)