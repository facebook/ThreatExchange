import unittest
import binascii

from pytx3.hashing.pdq_faiss_matcher import PDQFlatHashIndex, PDQMultiHashIndex

test_hashes = [
    "0000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000ffff",
    "0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f",
    "f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0",
    "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
]


class MixinTests:
    class PDQHashIndexSearchCommonTests(unittest.TestCase):
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


class TestPDQFlatHashIndex(MixinTests.PDQHashIndexSearchCommonTests, unittest.TestCase):
    def setUp(self):
        self.index = PDQFlatHashIndex.create(test_hashes)

    def test_create_faiss_index_from_hashes(self):
        assert type(self.index) is PDQFlatHashIndex
        hashes_as_bytes = [binascii.unhexlify(h) for h in test_hashes]

        assert self.index.faiss_index is not None
        assert self.index.faiss_index.ntotal == len(test_hashes)

        assert self.index.dataset_hashes is not None
        assert self.index.dataset_hashes == hashes_as_bytes


class TestPDQMultiHashIndex(
    MixinTests.PDQHashIndexSearchCommonTests, unittest.TestCase
):
    def setUp(self):
        self.index = PDQMultiHashIndex.create(test_hashes)

    def test_create_faiss_index_from_hashes(self):
        assert type(self.index) is PDQMultiHashIndex
        hashes_as_bytes = [binascii.unhexlify(h) for h in test_hashes]

        assert self.index.faiss_index is not None
        assert self.index.faiss_index.ntotal == len(test_hashes)

        assert self.index.dataset_hashes is not None
        assert self.index.dataset_hashes == hashes_as_bytes


if __name__ == "__main__":
    unittest.main()
