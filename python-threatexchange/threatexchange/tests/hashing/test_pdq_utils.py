# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import unittest
import binascii
import random

from threatexchange.signal_type.pdq.pdq_utils import *
from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.tests.hashing.utils import (
    get_zero_hash,
    get_random_hash,
    get_similar_hash,
)


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

    def test_binary_to_hex(self):
        for test_hash in test_hashes:
            bin_hash = hex_to_binary_str(test_hash)
            self.assertEqual(binary_str_to_hex(bin_hash), test_hash)

    def test_get_random_hash(self):
        for i in range(100):
            random_hash = get_random_hash()
            self.assertTrue(PdqSignal.validate_signal_str(random_hash))

    def test_get_similar_hash(self):
        for i in range(10):
            random_dist = random.randint(0, BITS_IN_PDQ)
            random_hash = get_random_hash()
            similar_hash = get_similar_hash(random_hash, random_dist)
            self.assertEqual(simple_distance(similar_hash, random_hash), random_dist)
        random_hash = get_random_hash()
        self.assertEqual(get_similar_hash(random_hash, 0), random_hash)
        # Max dist
        get_similar_hash(get_random_hash(), BITS_IN_PDQ)
        # Invalid dist
        self.assertRaises(
            ValueError, get_similar_hash, get_random_hash(), BITS_IN_PDQ + 1
        )
        self.assertRaises(ValueError, get_similar_hash, get_random_hash(), -1)

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
