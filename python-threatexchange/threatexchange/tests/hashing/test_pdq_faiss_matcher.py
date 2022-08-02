# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest
import binascii
import pickle
import numpy

from threatexchange.signal_type.pdq.pdq_faiss_matcher import (
    PDQFlatHashIndex,
    PDQMultiHashIndex,
)

test_hashes = [
    "0000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000ffff",
    "0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f",
    "f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0",
    "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
]

MAX_UNSIGNED_INT64 = numpy.iinfo(numpy.uint64).max


class MixinTests:
    class PDQHashIndexCommonTests(unittest.TestCase):
        index = None

        def assertEqualPDQHashSearchResults(self, result, expected):
            self.assertEqual(
                len(result), len(expected), "search results not of expected length"
            )
            for (r, e) in zip(result, expected):
                self.assertCountEqual(r, e)

        def test_search_index_for_exact_matches(self):
            query = test_hashes[:1]
            result = self.index.search(query, 0)
            self.assertEqualPDQHashSearchResults(result, [[q] for q in query])

        def test_search_index_for_near_matches(self):
            query = test_hashes[:1]
            result = self.index.search(query, 16)
            self.assertEqualPDQHashSearchResults(result, [test_hashes[:2]])

        def test_search_index_for_far_match(self):
            query = test_hashes[:1]
            result = self.index.search(query, 128)
            self.assertEqualPDQHashSearchResults(result, [test_hashes[:-1]])

        def test_search_index_multiple_queries(self):
            query = test_hashes
            result = self.index.search(query, 0)
            self.assertEqualPDQHashSearchResults(result, [[h] for h in test_hashes])

        def test_search_index_with_no_match(self):
            query = ["aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"]
            result = self.index.search(query, 0)
            self.assertEqualPDQHashSearchResults(result, [[]])

        def test_search_index_with_multiple_no_matches(self):
            query = [
                "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            ]
            result = self.index.search(query, 0)
            self.assertEqualPDQHashSearchResults(result, [[], []])

        def test_search_index_with_multiple_mixed_results(self):
            query = [
                "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                test_hashes[-1],
            ]
            result = self.index.search(query, 0)
            self.assertEqualPDQHashSearchResults(result, [[], [], [test_hashes[-1]]])

        def test_supports_pickling(self):
            pickled_data = pickle.dumps(self.index)
            assert (
                pickled_data != None
            ), "index does not support pickling to a data stream"

            reconstructed_index = pickle.loads(pickled_data)
            assert (
                reconstructed_index != None
            ), "index does not support unpickling from data stream"
            assert (
                reconstructed_index.faiss_index != self.index.faiss_index
            ), "unpickling should create it's own faiss index in memory"

            query = [test_hashes[0]]
            result = reconstructed_index.search(query, 0)
            self.assertEqualPDQHashSearchResults(result, [[test_hashes[0]]])


class TestPDQFlatHashIndex(MixinTests.PDQHashIndexCommonTests, unittest.TestCase):
    def setUp(self):
        self.index = PDQFlatHashIndex()
        self.index.add(test_hashes, range(0, len(test_hashes)))

    def test_create_faiss_index_from_hashes(self):
        assert type(self.index) is PDQFlatHashIndex
        hashes_as_bytes = [binascii.unhexlify(h) for h in test_hashes]

        assert self.index.faiss_index is not None
        assert self.index.faiss_index.ntotal == len(test_hashes)

    def test_hash_at(self):
        assert test_hashes[2] == self.index.hash_at(2)

    def test_search_index_return_ids(self):
        query = test_hashes[:2]
        results = self.index.search(query, 16, return_as_ids=True)
        self.assertEqualPDQHashSearchResults(results, [[0, 1], [0, 1]])


class TestPDQFlatHashIndexWithCustomIds(
    MixinTests.PDQHashIndexCommonTests, unittest.TestCase
):

    custom_ids = [MAX_UNSIGNED_INT64 - i for i in range(len(test_hashes))]

    def setUp(self):
        self.index = PDQFlatHashIndex()
        self.index.add(test_hashes, self.custom_ids)

    def test_create_faiss_index_from_hashes(self):
        assert type(self.index) is PDQFlatHashIndex
        hashes_as_bytes = [binascii.unhexlify(h) for h in test_hashes]

        assert self.index.faiss_index is not None
        assert self.index.faiss_index.ntotal == len(test_hashes)

    def test_hash_at(self):
        assert test_hashes[2] == self.index.hash_at(self.custom_ids[2])

    def test_search_index_return_ids(self):
        query = test_hashes[:2]
        results = self.index.search(query, 16, return_as_ids=True)
        self.assertEqualPDQHashSearchResults(
            results, [self.custom_ids[:2], self.custom_ids[:2]]
        )


class TestPDQMultiHashIndex(MixinTests.PDQHashIndexCommonTests, unittest.TestCase):
    def setUp(self):
        self.index = PDQMultiHashIndex()
        self.index.add(test_hashes, range(0, len(test_hashes)))

    def test_create_faiss_index_from_hashes(self):
        assert type(self.index) is PDQMultiHashIndex
        hashes_as_bytes = [binascii.unhexlify(h) for h in test_hashes]

        assert self.index.faiss_index is not None
        assert self.index.faiss_index.ntotal == len(test_hashes)

    def test_hash_at(self):
        assert test_hashes[2] == self.index.hash_at(2)

    def test_search_index_return_ids(self):
        query = test_hashes[:2]
        results = self.index.search(query, 16, return_as_ids=True)
        self.assertEqualPDQHashSearchResults(results, [[0, 1], [0, 1]])


class TestPDQMultiHashIndexWithCustomIds(
    MixinTests.PDQHashIndexCommonTests, unittest.TestCase
):
    custom_ids = [MAX_UNSIGNED_INT64 - i for i in range(len(test_hashes))]

    def setUp(self):
        self.index = PDQMultiHashIndex()
        self.index.add(test_hashes, custom_ids=self.custom_ids)

    def test_create_faiss_index_from_hashes(self):
        assert type(self.index) is PDQMultiHashIndex
        hashes_as_bytes = [binascii.unhexlify(h) for h in test_hashes]

        assert self.index.faiss_index is not None
        assert self.index.faiss_index.ntotal == len(test_hashes)

    def test_hash_at(self):
        assert test_hashes[2] == self.index.hash_at(self.custom_ids[2])

    def test_search_index_return_ids(self):
        query = test_hashes[:2]
        results = self.index.search(query, 16, return_as_ids=True)
        self.assertEqualPDQHashSearchResults(
            results, [self.custom_ids[:2], self.custom_ids[:2]]
        )


if __name__ == "__main__":
    unittest.main()
