# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest
import binascii

from threatexchange.hashing.pdq_utils import *

test_hashes = [
    "0000000000000000000000000000000000000000000000000000000000000000",
    "0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f",
    "f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0",
    "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
]


class TestPDQUtils(unittest.TestCase):
    def test_hex_to_binary(self):
        for test_hash in test_hashes:
            bin_hash = hex_to_binary_str(test_hash)
            self.assertEqual(len(bin_hash), BITS_IN_PDQ)
        self.assertEqual(hex_to_binary_str(test_hashes[0]), "0" * BITS_IN_PDQ)
        self.assertEqual(hex_to_binary_str(test_hashes[-1]), "1" * BITS_IN_PDQ)
        self.assertEqual(
            hex_to_binary_str(test_hashes[1]), "00001111" * (BITS_IN_PDQ // 8)
        )

    def test_distance_binary(self):
        self.assertEqual(
            simple_distance_binary("0" * BITS_IN_PDQ, "1" * BITS_IN_PDQ), BITS_IN_PDQ
        )
        self.assertEqual(
            simple_distance_binary("0" * BITS_IN_PDQ, "0" * BITS_IN_PDQ), 0
        )
        self.assertEqual(
            simple_distance_binary(
                "0" * BITS_IN_PDQ, hex_to_binary_str(test_hashes[1])
            ),
            BITS_IN_PDQ // 2,
        )

    def test_distance(self):
        self.assertEqual(simple_distance(test_hashes[1], test_hashes[1]), 0)
        self.assertEqual(simple_distance(test_hashes[1], test_hashes[2]), BITS_IN_PDQ)
        self.assertEqual(
            simple_distance(test_hashes[1], test_hashes[3]), BITS_IN_PDQ // 2
        )

    def test_match_threshold(self):
        self.assertFalse(pdq_match(test_hashes[0], test_hashes[1], threshold=31))
        self.assertTrue(
            pdq_match(test_hashes[0], test_hashes[1], threshold=BITS_IN_PDQ)
        )
        self.assertTrue(pdq_match(test_hashes[0], test_hashes[0], threshold=0))
        self.assertFalse(pdq_match(test_hashes[0], test_hashes[1], threshold=0))
        self.assertTrue(pdq_match(test_hashes[1], test_hashes[3], BITS_IN_PDQ // 2))
        self.assertFalse(
            pdq_match(test_hashes[1], test_hashes[3], BITS_IN_PDQ // 2 - 1)
        )


if __name__ == "__main__":
    unittest.main()
