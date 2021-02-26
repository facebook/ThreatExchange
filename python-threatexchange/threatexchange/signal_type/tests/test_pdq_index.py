# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest
import pickle

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
        for (r, e) in zip(result, expected):
            assert r.distance == e.distance, "result distance does not match"
            self.assertDictEqual(r.metadata, e.metadata)

    def test_search_index_for_matches(self):
        entry_hash = test_entries[1][0]
        result = self.index.query(entry_hash)
        self.assertEqualPDQIndexMatchResults(
            result,
            [IndexMatch(-1, test_entries[1][1]), IndexMatch(-1, test_entries[0][1])],
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
            [IndexMatch(-1, test_entries[1][1]), IndexMatch(-1, test_entries[0][1])],
        )
