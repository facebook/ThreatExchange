#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the pdf signal type.
"""

import pathlib
import typing as t
import warnings
from io import StringIO

from ..descriptor import SimpleDescriptorRollup, ThreatDescriptor
from . import signal_base

TLSH_CONFIDENT_MATCH_THRESHOLD = 30
EXPECT_TLSH_HASH_LENGTH = 72
""" 
This is a new signal type not found on ThreatExchange, in order to test the implementation we
override this set of hashes we want to match with here.
 
ToDo: @BarrettOlson: make this override cleaner and configurable by signal type in the future 
"""
TEMP_MATCH_IMPLEMNTATION_CHECK_DB = [
    [
        "T145B2859FE708266211A3026277C7AEE5FF76402C636AD5BA2C2CC11C23A1F2957773D5",
        [["test"], 1],
    ]
]


class TLSHSignal(
    signal_base.SimpleSignalType, signal_base.FileHasher, signal_base.BytesHasher
):
    """
    Simple signal type for PDFs using TLSH

    Extracts the text from a given pdf using pdfminer.six and hashes it with TLSH

    """

    TYPE_TAG = "media_type_pdf"

    @classmethod
    def hash_from_file(cls, file: pathlib.Path) -> str:
        if not str(file).endswith(".pdf"):
            warnings.warn("File does not appear to be a pdf. ", category=UserWarning)
            return ""

        try:
            import tlsh
            from pdfminer.converter import TextConverter
            from pdfminer.layout import LAParams
            from pdfminer.pdfdocument import PDFDocument
            from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
            from pdfminer.pdfpage import PDFPage
            from pdfminer.pdfparser import PDFParser
        except:
            warnings.warn(
                "Getting the tlsh hash of a pdf requires additional libraries already be installed; install threatexchange with the [pdf] extra",
                category=UserWarning,
            )
            return ""
        text = StringIO()
        with open(file, "rb") as in_file:
            parser = PDFParser(in_file)
            doc = PDFDocument(parser)
            rsrcmgr = PDFResourceManager()
            device = TextConverter(rsrcmgr, text, laparams=LAParams())
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            for page in PDFPage.create_pages(doc):
                interpreter.process_page(page)
            return str(tlsh.hash(text.getvalue().encode()))

    def match_hash(self, signal_str: str) -> t.List[signal_base.SignalMatch]:
        matches = []
        try:
            import tlsh
        except:
            warnings.warn(
                "Matching a tlsh hash requires additional libraries already be installed; install threatexchange with the [pdf] extra",
                category=UserWarning,
            )
            return []
        if len(signal_str) == EXPECT_TLSH_HASH_LENGTH:
            for x in TEMP_MATCH_IMPLEMNTATION_CHECK_DB:
                if tlsh.diffxlen(x[0], signal_str) <= TLSH_CONFIDENT_MATCH_THRESHOLD:
                    matches.append(signal_base.SignalMatch(x[1][0], x[1][1]))
        return matches
