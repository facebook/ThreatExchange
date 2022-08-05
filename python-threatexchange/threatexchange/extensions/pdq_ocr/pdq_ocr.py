# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the Photo PDQ plus OCR signal type.
Requires the installations of Optical character recognition (OCR) tools
"""

import typing as t
import pathlib

from threatexchange.content_type.content_base import ContentType
from threatexchange.content_type.photo import PhotoContent

from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.raw_text import RawTextSignal
from threatexchange.signal_type import signal_base
from threatexchange.exchanges.impl.fb_threatexchange_signal import (
    HasFbThreatExchangeIndicatorType,
)

from threatexchange.signal_type.pdq.pdq_hasher import pdq_from_file
from threatexchange.extensions.pdq_ocr.ocr_utils import text_from_image_file


class PdqOcrSignal(
    signal_base.SimpleSignalType,
    signal_base.FileHasher,
    HasFbThreatExchangeIndicatorType,
):
    """
    PDQ is an open source photo similarity algorithm. See 'pdq.py'
    This signal type combines pdq hashes with a text string found using
    optical character recognition (OCR) on the image hashed. This adds an
    additional 'distance' using levenshtein string comparison.

    Accuracy of matches will depend on quality of OCR implementations and selected thresholds.
    (ocr_utils uses the open source pytesseract wrapper of tesseract)
    """

    INDICATOR_TYPE = "HASH_PDQ_OCR"

    # This may need to be updated (TODO make more configurable)
    # Hashes of distance less than or equal to this threshold are considered a 'match'
    PDQ_PLUS_OCR_CONFIDENT_MATCH_THRESHOLD = 31
    # Match considered if 90% of the strings match
    LEVENSHTEIN_DISTANCE_PERCENT_THRESHOLD = 90

    @classmethod
    def get_content_types(cls) -> t.List[t.Type[ContentType]]:
        return [PhotoContent]

    @classmethod
    def hash_from_file(cls, file: pathlib.Path) -> str:
        pdq_hash, quality = pdq_from_file(file)
        ocr_text = text_from_image_file(file)

        return f"{pdq_hash},{ocr_text}"

    @classmethod
    def compare_hash(
        cls,
        hash1: str,
        hash2: str,
        pdq_dist_threshold: int = PDQ_PLUS_OCR_CONFIDENT_MATCH_THRESHOLD,
    ) -> signal_base.SignalComparisonResult:
        assert 0 <= pdq_dist_threshold <= 256
        pdq_hash_1, _, ocr_text_1 = hash1.partition(",")
        pdq_hash_2, _, ocr_text_2 = hash2.partition(",")
        assert all(
            (pdq_hash_1, ocr_text_1, pdq_hash_2, ocr_text_2)
        ), "malformed pdq_ocr hash"

        pdq_result = PdqSignal.compare_hash(pdq_hash_1, pdq_hash_2, pdq_dist_threshold)
        if not pdq_result.match:
            return pdq_result
        text_result = RawTextSignal.matches_str(
            ocr_text_1, ocr_text_2, cls.LEVENSHTEIN_DISTANCE_PERCENT_THRESHOLD
        )
        return signal_base.SignalComparisonResult(
            text_result.match, pdq_result.distance
        )

    @staticmethod
    def get_examples() -> t.List[str]:
        return [
            "a72dd3eadec2800ba74b59a9532d0b22011fd9e0daa1da3f576e602db999a754,This is a sample text string",
            "b2539a60de78841da72fcdeb5da21bf00185632ddaadb23d174ea1885999cb65,This is a sample text string",
        ]
