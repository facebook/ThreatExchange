#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the Photo PDQ plus OCR signal type.
Requires the installations of Optical character recognition (OCR) tools
"""

import math
import typing as t
import pathlib
import warnings

import Levenshtein

from ..descriptor import SimpleDescriptorRollup, ThreatDescriptor
from . import signal_base
from ..hashing.pdq_utils import pdq_match
from .. import common


class PdqOcrSignal(signal_base.SimpleSignalType, signal_base.FileHasher):
    """
    PDQ is an open source photo similarity algorithm. See 'pdq.py'
    This signal type combines pdq hashes with a text string found using
    optical character recognition (OCR) on the image hashed. This adds an
    additional 'distance' using levenshtein string comparison.

    Accuracy of matches will depend on quality of OCR implementations and selected thresholds.
    (ocr_utils uses the open source pytesseract wrapper of tesseract)
    """

    INDICATOR_TYPE = "HASH_PDQ_OCR"
    TYPE_TAG = "media_type_photo"

    # This may need to be updated (TODO make more configurable)
    # Hashes of distance less than or equal to this threshold are considered a 'match'
    PDQ_PLUS_OCR_CONFIDENT_MATCH_THRESHOLD = 31
    # Match considered if 90% of the strings match
    LEVENSHTEIN_DISTANCE_PERCENT_THRESHOLD = 0.10

    @classmethod
    def hash_from_file(cls, file: pathlib.Path) -> str:
        try:
            from ..hashing.pdq_hasher import pdq_from_file
            from ..hashing.ocr_utils import text_from_image_file
        except:
            warnings.warn(
                "Getting both PDQ hash and text of an image file using OCR requires additional libraries already be installed; install threatexchange with the [pdq_hasher & ocr] extra and see ocr_utils.py",
                category=UserWarning,
            )
            return ""

        pdq_hash, quality = pdq_from_file(file)
        ocr_text = text_from_image_file(file)

        return f"{pdq_hash},{ocr_text}"

    def match_hash(self, signal_str: str) -> t.List[signal_base.SignalMatch]:
        content_pdq_hash, _, content_ocr_text = signal_str.partition(",")
        if not content_ocr_text:
            return []
        matches = []
        for pdq_hash_plus_ocr, signal_attr in self.state.items():
            te_pdq_hash, te_ocr_text = pdq_hash_plus_ocr.split(",", maxsplit=1)
            # PDQ Hash Match
            if pdq_match(
                te_pdq_hash,
                content_pdq_hash,
                self.PDQ_PLUS_OCR_CONFIDENT_MATCH_THRESHOLD,
            ):
                # Check for text match
                normalized_content_str = common.normalize_string(content_ocr_text)
                normalized_te_str = common.normalize_string(te_ocr_text)
                if self._levenshtein_text_match(
                    normalized_content_str,
                    normalized_te_str,
                    self.LEVENSHTEIN_DISTANCE_PERCENT_THRESHOLD,
                ):
                    matches.append(
                        signal_base.SignalMatch(
                            signal_attr.labels, signal_attr.first_descriptor_id
                        )
                    )
        return matches

    def _levenshtein_text_match(self, str_a: str, str_b: str, threshold: float) -> bool:
        """
        Returns true if strings match within the percent threshold using Levenshtein distance
        """
        # TODO find way to reuse similar code in raw_text.py without sacrificing performance.
        match_threshold = math.floor(len(str_a) * threshold)
        ldiff = abs(len(str_a) - len(str_b))
        # Filter out anything that can't possibly match due to len difference
        if ldiff > match_threshold:
            return False
        distance = Levenshtein.distance(str_a, str_b)
        return distance <= match_threshold
