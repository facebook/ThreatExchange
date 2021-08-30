#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the pdf signal type.
"""

import hashlib
import pathlib
import typing as t
from io import StringIO
import tlsh
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

from ..descriptor import SimpleDescriptorRollup, ThreatDescriptor
from . import signal_base

TLSH_CONFIDENT_MATCH_THRESHOLD = 30
temp_db = [
    [
        "T145B2859FE708266211A3026277C7AEE5FF76402C636AD5BA2C2CC11C23A1F2957773D5",
        ["test", 1],
    ]
]


class TLSHSignal(
    signal_base.SimpleSignalType, signal_base.FileHasher, signal_base.BytesHasher
):
    """
    Simple signal type for PDFs using TLSH

    Extracts the text from a given pdf using pdfminer.six and hashes it with TLSH

    """

    INDICATOR_TYPE = "HASH_PDF"
    TYPE_TAG = "media_type_pdf"

    @classmethod
    def hash_from_file(cls, file: pathlib.Path) -> str:
        if str(file).endswith(".pdf"):
            text = StringIO()
            in_file = open(file, "rb")
            parser = PDFParser(in_file)
            doc = PDFDocument(parser)
            rsrcmgr = PDFResourceManager()
            device = TextConverter(rsrcmgr, text, laparams=LAParams())
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            for page in PDFPage.create_pages(doc):
                interpreter.process_page(page)
            return str(tlsh.hash(text.getvalue().encode()))
        print("Please provide a pdf")

    def match_hash(self, signal_str: str) -> t.List[signal_base.SignalMatch]:
        if len(signal_str) == 72:
            for x in temp_db:
                if tlsh.diffxlen(x[0], signal_str) <= TLSH_CONFIDENT_MATCH_THRESHOLD:
                    return x
        return []
