# Copyright (c) Meta Platforms, Inc. and affiliates.

import base64
import pathlib
import tempfile
import unittest

from threatexchange.signal_type.pdq import pdq_hasher

RANDOM_IMAGE_BASE64 = """iVBORw0KGgoAAAANSUhEUgAAABoAAAAcCAYAAAB/E6/TAAABQGlDQ1BJQ0MgUHJvZmlsZQAAKJFj
YGASSCwoyGFhYGDIzSspCnJ3UoiIjFJgf8rAzMDDwMGgziCUmFxc4BgQ4ANUwgCjUcG3awyMIPqy
LsisbUEsbr4sN5Y9iTOwFjbIZsFUjwK4UlKLk4H0HyBOTC4oKmFgYEwAspXLSwpA7BYgW6QI6Cgg
ewaInQ5hrwGxkyDsA2A1IUHOQPYVIFsgOSMxBch+AmTrJCGJpyOxofaCAHuokbmlgRMBl5IBSlIr
SkC0c35BZVFmekaJgiMwhFIVPPOS9XQUjAyMDBkYQOENUf1ZDByOjGKnEGIF/gwMlmUMDEyJCLE4
FwaG7coMDPyFCDENoL/40xgYDkYXJBYlwh3A+I2lOM3YCMLmKWJgYP3x//9nWaCXdzEw/C36///3
3P///y5hYGC+ycBwoBAAJoJZwzimB1MAAACKZVhJZk1NACoAAAAIAAQBGgAFAAAAAQAAAD4BGwAF
AAAAAQAAAEYBKAADAAAAAQACAACHaQAEAAAAAQAAAE4AAAAAAAAAkAAAAAEAAACQAAAAAQADkoYA
BwAAABIAAAB4oAIABAAAAAEAAAAaoAMABAAAAAEAAAAcAAAAAEFTQ0lJAAAAU2NyZWVuc2hvdB0L
cNQAAAAJcEhZcwAAFiUAABYlAUlSJPAAAAHUaVRYdFhNTDpjb20uYWRvYmUueG1wAAAAAAA8eDp4
bXBtZXRhIHhtbG5zOng9ImFkb2JlOm5zOm1ldGEvIiB4OnhtcHRrPSJYTVAgQ29yZSA1LjQuMCI+
CiAgIDxyZGY6UkRGIHhtbG5zOnJkZj0iaHR0cDovL3d3dy53My5vcmcvMTk5OS8wMi8yMi1yZGYt
c3ludGF4LW5zIyI+CiAgICAgIDxyZGY6RGVzY3JpcHRpb24gcmRmOmFib3V0PSIiCiAgICAgICAg
ICAgIHhtbG5zOmV4aWY9Imh0dHA6Ly9ucy5hZG9iZS5jb20vZXhpZi8xLjAvIj4KICAgICAgICAg
PGV4aWY6UGl4ZWxYRGltZW5zaW9uPjI2PC9leGlmOlBpeGVsWERpbWVuc2lvbj4KICAgICAgICAg
PGV4aWY6VXNlckNvbW1lbnQ+U2NyZWVuc2hvdDwvZXhpZjpVc2VyQ29tbWVudD4KICAgICAgICAg
PGV4aWY6UGl4ZWxZRGltZW5zaW9uPjI4PC9leGlmOlBpeGVsWURpbWVuc2lvbj4KICAgICAgPC9y
ZGY6RGVzY3JpcHRpb24+CiAgIDwvcmRmOlJERj4KPC94OnhtcG1ldGE+ChyymmEAAAAcaURPVAAA
AAIAAAAAAAAADgAAACgAAAAOAAAADgAAAmByXymqAAACLElEQVRIDYRTO2wTQRB949zZvoS4MIYk
pgpIIJQGEYlUKIgCaFIh0UQoLS2RKKChixCIgAiIlCAEHULQQZMCmhQgUSIEdIkcG+zYJHeHnVtm
72Pvntcwxc3O7Mx789mjSqUiYJAOCO9/WXhXs/FlZwgVP4NNLxNGTuQDjOUCHBvZw7lSG6eLHVgw
wnSRKU1U+5PBne95vNzModVJJQu2iQCpFRm1CBcnfFw74qOUDZSb3rFL1BaE5W85rP7IYncvDpB4
jNstNiGR2iDDQ8CVSR+LTGiTXkxIVOWxLHxy8LHOkf+SAR11U+JCposBnp50cYDHmwitfa2J+XUH
G66pyr6WOC/x8VGuTGJFq+ud2Vd2BF7MuDheiMZD5We/xcZO3CZxhuAoqU2S3EktJR2fui+PEN7O
ujjInREet3rD7BtNsqC4W+a/ccLG/FEbhwuEDLt32wINH9hyA8y88rSG5aOZ3g+8nvWY6GFzMJGy
/PE88PyCg7OHrKgbw5cetdirjDaOWZySP8uD7R5ROjnJYf1mzsHcpJ2O0GxaaWp2+BtwscNcG+Fe
QyFSkMOUaHRnyhbWLu3TQQwW3d9mb4IhA5KzYKK7dYXIkM2uJ+cdLEzlzJeKl5YbiqUfCbd/SrpI
0o8h3tH65QJOjetjW/3s4eYHD1vh350A6OAhbtwU4Vbtvx01rxYxmtXBxlbqTBI/8xS+ySQsVQcT
xdWI66W+XFqqsi/aYaT7QrTrvwAAAP//WDKhWgAAAcFJREFUjVLPSwJBFH5P65B08JKSZUh56dy9
U39Fh6AQpF/0wygIScSICCKKIIKi6NApomtg0Dno0jkVs6ws0qAfdLDXzO66M+606sDuvvne9973
vtlBSBQI6iyKtikMXH5RsFoAQvxZCPEI2VNBjJhiHqUHxguCy3l8Wet1VHsjxJ7IbGwkKO6VKI2F
qWIZgpuvQoyXScII0XxlfpbRLVCivbHuEusi/QMDB28SwsIqocUH1dGKr7qggd3+9ReETkuiuaUG
YeFecqRnabXDQqu/XUq+QyL5YUtEmMuRdmIShdY6pV1j4fBJEQ6vPhlZvk2iFiHChEgxpTOQFbEc
rftFhRFhJCd62t06ox7YF2E6y1TsmHpX2uhShWbuFKwWgDCZsbEjymgrIDZGhFNZzS2f1vZEDK6r
mTsaT0uOrP34DAi0HbAmACcyCmaKcnG++C9h8Wx/E+symlKut85ib2Na2uk2oUqAY0zIaGQ64v31
2XQai/v8TjgbcQH65jOUL5Ur9f9+abdHwTGcMgfRBuIMi7DP7YTzcAt4WtnRXd480uDRN+RLvwrR
dLQXVIVCt/xUqx1ILJ/bAcdDLuj1OjT0DwULeQovxm67AAAAAElFTkSuQmCC"""

RANDOM_IMAGE_PDQ = "ad64cd9875e131a177b1f2a0d6b38ae1de9ea80421e4c51dde1b0363deba3466"


class PDQHasherModuleUnitTest(unittest.TestCase):
    def setUp(self):
        """Set up test images."""
        self.test_files = {
            # Grayscale with alpha channel
            "la": {
                "path": "threatexchange/tests/hashing/resources/LA.png",
                "expected_pdq": "accb6d39648035f8125c8ce6ba65007de7b54c67a2d93ef7b8f33b0611306715",
                "expected_quality": 100,
            },
            # 16-bit grayscale
            "i16": {
                "path": "threatexchange/tests/hashing/resources/I16.png",
                "expected_pdq": "de2ef0e99ecdfc1d248a0eb055f023d1d61e79c3920cbb55d561c02accab1763",
                "expected_quality": 36,
            },
            # Standard RGB test
            "rgb": {
                "path": "threatexchange/tests/hashing/resources/rgb.jpeg",
                "expected_pdq": "fb4eed46cb8a6c78819ca06b756c541f7b07ef6d02c82fccd00f862166272cda",
                "expected_quality": 100,
            },
        }

    def test_pdq_from_file_different_formats(self):
        """Test PDQ hash computation from files of different formats."""
        for format_name, test_data in self.test_files.items():
            with self.subTest(format=format_name):
                file_path = pathlib.Path(test_data["path"])
                if file_path.exists():
                    pdq_hash, pdq_quality = pdq_hasher.pdq_from_file(file_path)
                    assert pdq_hash == test_data["expected_pdq"]
                    assert pdq_quality == test_data["expected_quality"]

    def test_pdq_from_bytes_different_formats(self):
        """Test PDQ hash computation from bytes of different formats."""
        for format_name, test_data in self.test_files.items():
            with self.subTest(format=format_name):
                file_path = pathlib.Path(test_data["path"])
                if file_path.exists():
                    with open(file_path, "rb") as f:
                        bytes_data = f.read()
                        pdq_hash, pdq_quality = pdq_hasher.pdq_from_bytes(bytes_data)
                        assert pdq_hash == test_data["expected_pdq"]
                        assert pdq_quality == test_data["expected_quality"]

    def test_pdq_from_file(self):
        """Writes a few bytes to a file and runs the pdq hasher on it."""
        with tempfile.NamedTemporaryFile("w+b") as f:
            f.write(base64.b64decode(RANDOM_IMAGE_BASE64))
            f.flush()

            pdq_hash = pdq_hasher.pdq_from_file(pathlib.Path(f.name))[0]
            assert pdq_hash == RANDOM_IMAGE_PDQ

    def test_pdq_from_bytes(self):
        """Runs the pdq hasher directly on bytes"""
        bytes_ = base64.b64decode(RANDOM_IMAGE_BASE64)
        pdq_hash = pdq_hasher.pdq_from_bytes(bytes_)[0]
        assert pdq_hash == RANDOM_IMAGE_PDQ
