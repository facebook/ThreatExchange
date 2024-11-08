import pickle
import typing as t
import pytest
import functools

from threatexchange.signal_type.index import (
    SignalSimilarityInfoWithIntDistance,
)
from threatexchange.signal_type.pdq.pdq_index import PDQIndex, PDQIndexMatch

test_entries = [
    (
        "0000000000000000000000000000000000000000000000000000000000000000",
        {"hash_type": "pdq", "system_id": 9},
    ),
    (
        "000000000000000000000000000000000000000000000000000000000000ffff",
        {"hash_type": "pdq", "system_id": 8},
    ),
    (
        "0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f",
        {"hash_type": "pdq", "system_id": 7},
    ),
    (
        "f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0",
        {"hash_type": "pdq", "system_id": 6},
    ),
    (
        "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        {"hash_type": "pdq", "system_id": 5},
    ),
]

@pytest.fixture
def index():
    return PDQIndex.build(test_entries)

def assert_equal_pdq_index_match_results(result: t.List[PDQIndexMatch], expected: t.List[PDQIndexMatch]):
    assert len(result) == len(expected), "search results not of expected length"

    def quality_indexed_dict_reducer(
        acc: t.Dict[int, t.Set[int]], item: PDQIndexMatch
    ) -> t.Dict[int, t.Set[int]]:
        acc[item.similarity_info.distance] = acc.get(item.similarity_info.distance, set())
        acc[item.similarity_info.distance].add(hash(frozenset(item.metadata)))
        return acc

    distance_to_result_items_map = functools.reduce(quality_indexed_dict_reducer, result, {})
    distance_to_expected_items_map = functools.reduce(quality_indexed_dict_reducer, expected, {})

    assert len(distance_to_expected_items_map) == len(distance_to_result_items_map), "Unequal number of items"

    for distance, result_items in distance_to_result_items_map.items():
        assert distance in distance_to_expected_items_map, f"Unexpected distance {distance} found"
        assert result_items == distance_to_expected_items_map[distance]

def test_search_index_for_matches(index):
    entry_hash = test_entries[1][0]
    result = index.query(entry_hash)
    assert_equal_pdq_index_match_results(
        result,
        [
            PDQIndexMatch(SignalSimilarityInfoWithIntDistance(0), test_entries[1][1]),
            PDQIndexMatch(SignalSimilarityInfoWithIntDistance(16), test_entries[0][1]),
        ],
    )

def test_search_index_with_no_match(index):
    query_hash = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    result = index.query(query_hash)
    assert_equal_pdq_index_match_results(result, [])

def test_supports_pickling(index):
    pickled_data = pickle.dumps(index)
    assert pickled_data is not None, "index does not support pickling to a data stream"

    reconstructed_index = pickle.loads(pickled_data)
    assert reconstructed_index is not None, "index does not support unpickling from data stream"
    assert reconstructed_index.index.faiss_index != index.index.faiss_index, "unpickling should create its own faiss index in memory"

    query = test_entries[0][0]
    result = reconstructed_index.query(query)
    assert_equal_pdq_index_match_results(
        result,
        [
            PDQIndexMatch(SignalSimilarityInfoWithIntDistance(0), test_entries[1][1]),
            PDQIndexMatch(SignalSimilarityInfoWithIntDistance(16), test_entries[0][1]),
        ],
    )
