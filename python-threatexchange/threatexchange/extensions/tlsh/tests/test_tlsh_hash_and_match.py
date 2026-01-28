# Copyright (c) Meta Platforms, Inc. and affiliates.
import unittest

try:
    import tlsh as _

    _DISABLED = False
except ImportError:
    _DISABLED = True
else:
    from threatexchange.extensions.tlsh.text_tlsh import TextTLSHSignal


@unittest.skipIf(_DISABLED, "tlsh not installed")
class TLSHHasherModuleUnitTest(unittest.TestCase):
    def test_tlsh_from_string(self):
        expected = {
            "A minimum string length must be 256 bytes! "
            "That's so much text this means it's not super "
            "useful for finding short text!": "T1DFB092A1724AC2C0D3CA48452291E"
            "A04A5B75EB903A6E7577A54118FFA8148E98F9426",
            "too short": "",
        }
        for input, expected_hash in expected.items():
            hashed = TextTLSHSignal.hash_from_str(input)

        assert hashed == expected_hash, f"case: {input}"
