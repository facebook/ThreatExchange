# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import unittest

from threatexchange.signal_type import tlsh_pdf

TEST_PDF_COMPLETE_TLSH = (
    "T145B2859FE708266211A3026277C7AEE5FF76402C636AD5BA2C2CC11C23A1F2957773D5"
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
        assert tlsh_complete_data_hash == TEST_PDF_COMPLETE_TLSH
        assert tlsh_complete_match != []
        assert tlsh_half_complete_match != []
