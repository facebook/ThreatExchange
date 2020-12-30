#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the Photo PDQ signal type.
"""

import typing as t
import pathlib
import warnings

from ..descriptor import SimpleDescriptorRollup, ThreatDescriptor
from . import signal_base
from ..hashing.pdq_utils import pdq_match, BITS_IN_PDQ


class PdqSignal(signal_base.SimpleSignalType, signal_base.FileMatcher):
    """
    PDQ is an open source photo similarity algorithm.

    Unlike MD5s, which are sensitive to single pixel differences, PDQ has
    a concept of "distance" and can detect when content is visually similar.
    This property tends to make it much more effective at finding images that
    a human would claim are the same, but also opens the door for false
    positives.

    Which distance to use can differ based on the type of content being
    searched for. While the PDQ documentation suggests certain thresholds,
    they can sometimes vary depending on what you are comparing against.
    """

    INDICATOR_TYPE = "HASH_PDQ"
    TYPE_TAG = "media_type_photo"

    # This may need to be updated (TODO make more configurable)
    # Hashes of distance less than or equal to this threshold are considered a 'match'
    PDQ_CONFIDENT_MATCH_THRESHOLD = 31

    def match_file(self, file: pathlib.Path) -> t.List[signal_base.SignalMatch]:
        """Simple PDQ file match."""
        try:
            from threatexchange.hashing.pdq_hasher import pdq_from_file
        except:
            warnings.warn(
                "PDQ from file require Pillow and pdqhash to be installed; install threatexchange with the [pdq_hasher] extra to use them",
                category=UserWarning,
            )
            return []
        pdq_hash, quality = pdq_from_file(file)
        return self.match_hash(pdq_hash)

    def match_hash(self, signal_str: str) -> t.List[signal_base.SignalMatch]:

        # for case where cli tries to match against non-pdq type hashes
        # (filtering should likely be moved up in future to avoid silent errors)
        if len(signal_str) != BITS_IN_PDQ / 4:
            return []

        return [
            signal_base.SignalMatch(signal_attr.labels, signal_attr.first_descriptor_id)
            for pdq_hash, signal_attr in self.state.items()
            if pdq_match(pdq_hash, signal_str, self.PDQ_CONFIDENT_MATCH_THRESHOLD)
        ]
