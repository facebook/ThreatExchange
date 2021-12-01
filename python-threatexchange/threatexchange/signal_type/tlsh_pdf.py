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


class TLSHSignal(
    signal_base.SimpleSignalType, signal_base.FileHasher, signal_base.BytesHasher
):
    """
    Simple signal type for PDFs using TLSH

    Extracts the text from a given pdf using pdfminer.six and hashes it with TLSH

    """

    INDICATOR_TYPE = "HASH_TEXT_TLSH"
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
            for tlsh_hash, signal_attr in self.state.items():
                if (
                    tlsh.diffxlen(tlsh_hash, signal_str)
                    <= TLSH_CONFIDENT_MATCH_THRESHOLD
                ):
                    matches.append(
                        signal_base.SignalMatch(
                            signal_attr.labels, signal_attr.first_descriptor_id
                        )
                    )
        return matches
