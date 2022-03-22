#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the pdf signal type.
"""

import typing as t
import pathlib
import warnings
from io import StringIO
from threatexchange.content_type.content_base import ContentType
from threatexchange.content_type.text import TextContent

from threatexchange.signal_type import signal_base
from threatexchange.signal_type.raw_text import RawTextSignal

TLSH_CONFIDENT_MATCH_THRESHOLD = 30
EXPECT_TLSH_HASH_LENGTH = 72

try:
    import tlsh

    # TODO Restore
    # from pdfminer.converter import TextConverter
    # from pdfminer.layout import LAParams
    # from pdfminer.pdfdocument import PDFDocument
    # from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
    # from pdfminer.pdfpage import PDFPage
    # from pdfminer.pdfparser import PDFParser

    _ENABLED = True
except ImportError:
    _ENABLED = False


class TLSHSignal(
    signal_base.SimpleSignalType,
    signal_base.BytesHasher,
    signal_base.TextHasher,
):
    """
    Simple signal type for text using TLSH

    Extracts the text from a given pdf using pdfminer.six and hashes it with TLSH

    """

    INDICATOR_TYPE = "HASH_TEXT_TLSH"

    @classmethod
    def get_content_types(self) -> t.List[t.Type[ContentType]]:
        return [TextContent]

    @classmethod
    def hash_from_str(cls, text: str) -> str:
        return cls.hash_from_bytes(text.encode())

    @classmethod
    def hash_from_bytes(cls, bytes_: bytes) -> str:
        assert _ENABLED
        return str(tlsh.hash(bytes_))

    @classmethod
    def compare_hash(
        cls, hash1: str, hash2: str, distance_threshold: t.Optional[int] = None
    ) -> signal_base.HashComparisonResult:
        if distance_threshold is None:
            distance_threshold = TLSH_CONFIDENT_MATCH_THRESHOLD
        dist = tlsh.diffxlen(hash1, hash2)
        return signal_base.HashComparisonResult.from_dist(dist, distance_threshold)

    @staticmethod
    def get_examples() -> t.List[str]:
        return [TLSHSignal.hash_from_str(s) for s in RawTextSignal.get_examples()]
