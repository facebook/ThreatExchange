# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the pdf signal type.
"""

import re
import typing as t
from threatexchange.content_type.content_base import ContentType
from threatexchange.content_type.text import TextContent

from threatexchange.signal_type import signal_base
from threatexchange.signal_type.raw_text import RawTextSignal

import tlsh

TLSH_CONFIDENT_MATCH_THRESHOLD = 30
EXPECT_TLSH_HASH_LENGTH = 72


class TextTLSHSignal(signal_base.SimpleSignalType, signal_base.TextHasher):
    """
    Simple signal type for text using TLSH.

    Read about TLSH at https://github.com/trendmicro/tlsh
    """

    INDICATOR_TYPE = "HASH_TEXT_TLSH"

    @classmethod
    def get_content_types(cls) -> t.List[t.Type[ContentType]]:
        return [TextContent]

    @classmethod
    def validate_signal_str(cls, signal_str: str) -> str:
        """'T1' followed 70 hexidecimal characters. Total length 72 characters."""
        if not re.match("^T1[0-9A-F]{70}$", signal_str):
            raise ValueError("invalid TLSH hash")
        return signal_str

    @classmethod
    def hash_from_str(cls, text: str) -> str:
        hash_str = str(tlsh.hash(text.encode()))
        if hash_str == "TNULL":  # Likely too short
            return ""
        return hash_str

    @classmethod
    def compare_hash(
        cls,
        hash1: str,
        hash2: str,
        tlsh_threshold: int = TLSH_CONFIDENT_MATCH_THRESHOLD,
    ) -> signal_base.SignalComparisonResult:
        dist: int = tlsh.diffxlen(hash1, hash2)
        return signal_base.SignalComparisonResult.from_simple_dist(dist, tlsh_threshold)

    @staticmethod
    def get_examples() -> t.List[str]:
        return [TextTLSHSignal.hash_from_str(s) for s in RawTextSignal.get_examples()]
