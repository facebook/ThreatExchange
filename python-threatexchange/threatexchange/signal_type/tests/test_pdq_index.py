# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest
import pickle
import typing as t
import functools

from threatexchange.signal_type.index import IndexMatch
from threatexchange.signal_type.pdq_index import PDQIndex

test_entries = [
    (
        "0000000000000000000000000000000000000000000000000000000000000000",
        dict(
            {
                "hash_type": "pdq",
                "system_id": 9,
            }
        ),
    ),
    (
        "000000000000000000000000000000000000000000000000000000000000ffff",
        dict(
            {
                "hash_type": "pdq",
                "system_id": 8,
            }
        ),
    ),
    (
        "0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f",
        dict(
            {
                "hash_type": "pdq",
                "system_id": 7,
            }
        ),
    ),
    (
        "f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0",
        dict(
            {
                "hash_type": "pdq",
                "system_id": 6,
            }
        ),
    ),
    (
        "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        dict(
            {
                "hash_type": "pdq",
                "system_id": 5,
            }
        ),
    ),
]


class TestPDQIndex(unittest.TestCase):
    def setUp(self):
        self.index = PDQIndex.build(test_entries)

    def assertEqualPDQIndexMatchResults(self, result, expected):
        self.assertEqual(
            len(result), len(expected), "search results not of expected length"
        )

        # Between python 3.8.6 and 3.8.11, something caused the order of results
        # from the index to change. This was noticed for items which had the
        # same distance. To allow for this, we convert result and expected
        # arrays from
        #   [IndexMatch, IndexMatch] to { distance: <set of IndexMatch.metadata hash> }
        # This allows you to compare [IndexMatch A, IndexMatch B] with
        # [IndexMatch B, IndexMatch A] as long as A.distance == B.distance.

        def quality_indexed_dict_reducer(acc, item):
            acc[item.distance] = acc.get(item.distance, set())
            # Instead of storing the unhashable item.metadata dict, store its
            # hash so we can compare using self.assertSetEqual
            acc[item.distance].add(hash(frozenset(item.metadata)))
            return acc

        # Convert results to distance -> set of metadata map
        distance_to_result_items_map: t.Dict[int, t.Set[t.Dict]] = functools.reduce(
            quality_indexed_dict_reducer, result, dict()
        )

        # Convert expected to distance -> set of metadata map
        distance_to_expected_items_map: t.Dict[int, t.Set[t.Dict]] = functools.reduce(
            quality_indexed_dict_reducer, expected, dict()
        )

        assert len(distance_to_expected_items_map) == len(
            distance_to_result_items_map
        ), "Unequal number of items in expected and results."

        for distance, result_items in distance_to_result_items_map.items():
            assert (
                distance in distance_to_expected_items_map
            ), f"Unexpected distance {distance} found"
            self.assertSetEqual(result_items, distance_to_expected_items_map[distance])

    def test_search_index_for_matches(self):
        entry_hash = test_entries[1][0]
        result = self.index.query(entry_hash)
        self.assertEqualPDQIndexMatchResults(
            result,
            [IndexMatch(0, test_entries[1][1]), IndexMatch(16, test_entries[0][1])],
        )

    def test_search_index_with_no_match(self):
        query_hash = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        result = self.index.query(query_hash)
        self.assertEqualPDQIndexMatchResults(result, [])

    def test_supports_pickling(self):
        pickled_data = pickle.dumps(self.index)
        assert pickled_data != None, "index does not support pickling to a data stream"

        reconstructed_index = pickle.loads(pickled_data)
        assert (
            reconstructed_index != None
        ), "index does not support unpickling from data stream"
        assert (
            reconstructed_index.index.faiss_index != self.index.index.faiss_index
        ), "unpickling should create it's own faiss index in memory"

        query = test_entries[0][0]
        result = reconstructed_index.query(query)
        self.assertEqualPDQIndexMatchResults(
            result,
            [IndexMatch(0, test_entries[1][1]), IndexMatch(16, test_entries[0][1])],
        )
