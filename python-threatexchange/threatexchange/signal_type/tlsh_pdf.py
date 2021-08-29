#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the pdf signal type.
"""

import hashlib
import pathlib
import typing as t
import tlsh
import fitz

from ..descriptor import SimpleDescriptorRollup, ThreatDescriptor
from . import signal_base

TLSH_CONFIDENT_MATCH_THRESHOLD = 30
temp_db = [["T1B7B2759FD708166211A2026277C7AAE5FF35806C7366E5BA2C2C815C33A1F39537B3E5", ["test", 1]]]

class TLSHSignal(
    signal_base.SimpleSignalType, signal_base.FileHasher, signal_base.BytesHasher
):
    """
    Simple signal type for PDFs using TLSH

    Extracts the text from a given pdf using PyMuPDF and hashes it with TLSH

    """

    INDICATOR_TYPE = "HASH_PDF"
    TYPE_TAG = "media_type_pdf"

    @classmethod
    def hash_from_file(cls, file: pathlib.Path) -> str:
        text = ""
        with fitz.open(file) as pdf_file:
            for page in pdf_file:
                page_text = page.getText()
                if len(page_text) > 0:
                    text +=page_text
        return str(tlsh.hash(text.encode()))

    def match_hash(self, signal_str: str) -> t.List[signal_base.SignalMatch]:
        if len(signal_str) == 72:
            for x in temp_db:
                if tlsh.diffxlen(x[0], signal_str) <= TLSH_CONFIDENT_MATCH_THRESHOLD:
                    return x
        return []
        