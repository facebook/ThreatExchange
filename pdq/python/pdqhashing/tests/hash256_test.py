# pyre-strict
# Copyright (c) Meta Platforms, Inc. and affiliates.
from pdqhashing.types.exceptions import PDQHashFormatException
from pdqhashing.types.hash256 import Hash256
import unittest


class Hash256Test(unittest.TestCase):
    SAMPLE_HASH = "9c151c3af838278e3ef57c180c7d031c07aefd12f2ccc1e18f2a1e1c7d0ff163"

    def test_incorrect_hex_length(self) -> None:
        with self.assertRaises(PDQHashFormatException):
            Hash256.fromHexString("AAA")

    def test_incorrect_hex_format(self) -> None:
        with self.assertRaises(PDQHashFormatException):
            Hash256.fromHexString(
                "9c151c3af838278e3ef57c180c7d031c07aefd12f2ccc1e18f2a1e1c7d0ff16!"
            )

    def test_correct_hex_format(self) -> None:
        hash = Hash256.fromHexString(self.SAMPLE_HASH)
        self.assertNotEqual(hash, None)

    def test_clone(self) -> None:
        hash = Hash256.fromHexString(self.SAMPLE_HASH)
        hash_copy = hash.clone()
        self.assertTrue(hash == hash_copy)

    def test_to_string(self) -> None:
        s = self.SAMPLE_HASH
        hash = Hash256.fromHexString(s)
        self.assertEqual(hash.__str__(), s)

    def test_bit_count(self) -> None:
        self.assertEqual(Hash256.bitCount(1), 1)
        self.assertEqual(Hash256.bitCount(100), 3)  # dec(10) = bin(01100100)

    def test_hamming_norm(self) -> None:
        hash = Hash256()
        hash.setAll()
        self.assertEqual(hash.hammingNorm(), 256)

        hash = Hash256.fromHexString(self.SAMPLE_HASH)
        self.assertEqual(hash.hammingNorm(), 128)

    def test_hamming_distance(self) -> None:
        hash1 = Hash256.fromHexString(self.SAMPLE_HASH)
        hash2 = Hash256()
        hash2.clearAll()
        self.assertEqual(hash1.hammingDistance(hash2), 128)

        hash1 = Hash256()
        hash1.setAll()
        hash2 = Hash256()
        hash2.clearAll()
        self.assertEqual(hash1.hammingDistance(hash2), 256)
        self.assertEqual(hash1.hammingDistanceLE(hash2, 1), False)
        self.assertEqual(hash1.hammingDistanceLE(hash2, 257), True)
        self.assertEqual(hash1.hammingDistanceLE(hash1, 0), True)

    def test_binary_operations(self) -> None:
        hash = Hash256.fromHexString(self.SAMPLE_HASH)

        self.assertTrue(hash.bitwiseAND(hash) == hash)

        hash_negative = hash.bitwiseNOT()
        self.assertTrue(hash.bitwiseAND(hash_negative) == Hash256())

        hash_set_all = Hash256()
        hash_set_all.setAll()

        self.assertEqual(hash.bitwiseOR(hash_negative), hash_set_all)
        self.assertEqual(hash.bitwiseXOR(hash_negative), hash_set_all)
