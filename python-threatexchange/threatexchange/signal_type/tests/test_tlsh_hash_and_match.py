# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import unittest

from threatexchange.signal_type import tlsh


@unittest.skipIf(not tlsh._ENABLED, "tlsh not installed")
class TLSHHasherModuleUnitTest(unittest.TestCase):
    def test_tlsh_from_string(self):
        expected = {
            "A minimum string length must be 256 bytes! "
            "That's so much text this means it's not super "
            "useful for finding short text!": "T1DFB092A1724AC2C0D3CA48452291E"
            "A04A5B75EB903A6E7577A54118FFA8148E98F9426",
        }
        for input, expected_hash in expected.items():
            hashed = tlsh.TLSHSignal.hash_from_str(input)

        assert hashed == expected_hash, f"case: {input}"
