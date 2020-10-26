import unittest
import binascii

import pytx3.hashing.pdq_faiss_matcher


class TestPDQFlatHashIndex(unittest.TestCase):

    test_hashes = [
        "0000000000000000000000000000000000000000000000000000000000000000",
        "000000000000000000000000000000000000000000000000000000000000ffff",
        "0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f",
        "f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0",
        "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
    ]

    def setUp(self):
        self.index = pytx3.hashing.pdq_faiss_matcher.PDQFlatHashIndex.create(
            self.test_hashes
        )

    def test_create_faiss_index_from_hashes(self):
        hashes_as_bytes = [binascii.unhexlify(h) for h in self.test_hashes]

        assert self.index.faiss_index is not None
        assert self.index.faiss_index.ntotal == len(self.test_hashes)

        assert self.index.dataset_hashes is not None
        assert self.index.dataset_hashes == hashes_as_bytes

    def test_search_index_for_exact_matches(self):
        query = self.test_hashes[:1]
        result = self.index.search(query, 0)
        assert result == [[q] for q in query]

    def test_search_index_for_near_matches(self):
        query = self.test_hashes[:1]
        result = self.index.search(query, 16)
        assert result == [self.test_hashes[:2]]

    def test_search_index_multiple_queries(self):
        query = self.test_hashes
        result = self.index.search(query, 0)
        assert result == [[h] for h in self.test_hashes]

    def test_search_index_with_no_match(self):
        query = ["aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"]
        result = self.index.search(query, 0)
        assert result == [[]]

    def test_search_index_with_multiple_no_matches(self):
        query = [
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        ]
        result = self.index.search(query, 0)
        assert result == [[], []]

    def test_search_index_with_multiple_mixed_results(self):
        query = [
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            self.test_hashes[-1],
        ]
        result = self.index.search(query, 0)
        assert result == [[], [], [self.test_hashes[-1]]]


if __name__ == "__main__":
    unittest.main()
