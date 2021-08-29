# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import base64
import pathlib
import tempfile
import unittest

from threatexchange.signal_type import tlsh_pdf

RANDOM_PDF_TLSH = (
    "T1B7B2759FD708166211A2026277C7AAE5FF35806C7366E5BA2C2C815C33A1F39537B3E5"
)


class TLSHHasherModuleUnitTest(unittest.TestCase):
    def test_tlsh_from_file(self):
        tlsh_complete_data_hash = tlsh_pdf.TLSHSignal.hash_from_file(
            "data/test_pdf_complete.pdf"
        )
        tlsh_half_data_hash = tlsh_pdf.TLSHSignal.hash_from_file(
            "data/test_pdf_half.pdf"
        )
        tlsh_complete_match = tlsh_pdf.TLSHSignal.match_hash(
            self, tlsh_complete_data_hash
        )
        tlsh_half_complete_match = tlsh_pdf.TLSHSignal.match_hash(
            self, tlsh_half_data_hash
        )
        assert tlsh_complete_data_hash == RANDOM_PDF_TLSH
        assert tlsh_complete_match != []
        assert tlsh_half_complete_match != []
