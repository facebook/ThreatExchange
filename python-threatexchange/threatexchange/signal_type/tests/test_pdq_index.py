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


def assert_equal_pdq_index_match_results(
    result: t.List[PDQIndexMatch], expected: t.List[PDQIndexMatch]
):
    assert len(result) == len(expected), "Search results not of expected length"

    def quality_indexed_dict_reducer(
        acc: t.Dict[int, t.Set[int]], item: PDQIndexMatch
    ) -> t.Dict[int, t.Set[int]]:
        acc[item.similarity_info.distance] = acc.get(
            item.similarity_info.distance, set()
        )
        acc[item.similarity_info.distance].add(hash(frozenset(item.metadata)))
        return acc

    distance_to_result_items_map: t.Dict[int, t.Set[int]] = functools.reduce(
        quality_indexed_dict_reducer, result, {}
    )
    distance_to_expected_items_map: t.Dict[int, t.Set[int]] = functools.reduce(
        quality_indexed_dict_reducer, expected, {}
    )

    assert len(distance_to_expected_items_map) == len(
        distance_to_result_items_map
    ), "Unequal number of distance groups"

    for distance, result_items in distance_to_result_items_map.items():
        assert (
            distance in distance_to_expected_items_map
        ), f"Unexpected distance {distance} found in results"
        assert result_items == distance_to_expected_items_map[distance], (
            f"Mismatch at distance {distance}. "
            f"Expected: {distance_to_expected_items_map[distance]}, Got: {result_items}"
        )


@pytest.mark.parametrize(
    "entry_hash, expected_matches",
    [
        (
            test_entries[1][0],
            [
                PDQIndexMatch(
                    SignalSimilarityInfoWithIntDistance(0), test_entries[1][1]
                ),
                PDQIndexMatch(
                    SignalSimilarityInfoWithIntDistance(16), test_entries[0][1]
                ),
            ],
        ),
        (
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            [],
        ),
    ],
)
def test_search_index(index, entry_hash, expected_matches):
    result = index.query(entry_hash)
    assert_equal_pdq_index_match_results(result, expected_matches)


def test_partial_match_below_threshold(index):
    query_hash = "ffffffffffffffffffffffffffffffffffffffffffffffffffffffff00000000"
    result = index.query(query_hash)
    assert_equal_pdq_index_match_results(result, [])


def test_supports_pickling(index):
    pickled_data = pickle.dumps(index)
    assert pickled_data is not None, "Index does not support pickling to a data stream"

    reconstructed_index = pickle.loads(pickled_data)
    assert (
        reconstructed_index is not None
    ), "Index does not support unpickling from data stream"
    assert (
        reconstructed_index.index.faiss_index != index.index.faiss_index
    ), "Unpickling should create its own FAISS index in memory"

    assert (
        len(reconstructed_index) == len(index)
    ), "Index size mismatch after unpickling"

    query = test_entries[0][0]
    result = reconstructed_index.query(query)
    assert_equal_pdq_index_match_results(
        result,
        [
            PDQIndexMatch(SignalSimilarityInfoWithIntDistance(0), test_entries[1][1]),
            PDQIndexMatch(SignalSimilarityInfoWithIntDistance(16), test_entries[0][1]),
        ],
    )
