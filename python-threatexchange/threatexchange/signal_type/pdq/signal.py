# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the Photo PDQ signal type.
"""

import typing as t
import re

from threatexchange.signal_type.pdq.pdq_hasher import pdq_from_bytes
from threatexchange.content_type.content_base import ContentType
from threatexchange.content_type.photo import PhotoContent
from threatexchange.signal_type import signal_base
from threatexchange.signal_type.pdq.pdq_utils import simple_distance
from threatexchange.exchanges.impl.fb_threatexchange_signal import (
    HasFbThreatExchangeIndicatorType,
)
from threatexchange.signal_type.pdq.pdq_index import PDQIndex


class PdqSignal(
    signal_base.SimpleSignalType,
    signal_base.BytesHasher,
    HasFbThreatExchangeIndicatorType,
):
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

    # This may need to be updated (TODO make more configurable)
    # Hashes of distance less than or equal to this threshold are considered a 'match'
    PDQ_CONFIDENT_MATCH_THRESHOLD = 31
    # Images with less than quality 50 are too unreliable to match on
    QUALITY_THRESHOLD = 50

    @classmethod
    def get_content_types(cls) -> t.List[t.Type[ContentType]]:
        return [PhotoContent]

    @classmethod
    def get_index_cls(cls) -> t.Type[PDQIndex]:
        return PDQIndex

    @classmethod
    def validate_signal_str(cls, signal_str: str) -> str:
        """PDQ hash contains 64 hexidecimal characters."""
        if not re.match("^[0-9a-f]{64}$", signal_str):
            raise ValueError("invalid PDQ hash")
        return signal_str

    @classmethod
    def compare_hash(
        cls,
        hash1: str,
        hash2: str,
        pdq_dist_threshold: int = PDQ_CONFIDENT_MATCH_THRESHOLD,
    ) -> signal_base.SignalComparisonResult:
        dist = simple_distance(hash1, hash2)
        return signal_base.SignalComparisonResult.from_simple_dist(
            dist, pdq_dist_threshold
        )

    @classmethod
    def hash_from_bytes(cls, bytes_: bytes) -> str:
        pdq_hash, quality = pdq_from_bytes(bytes_)
        if quality < cls.QUALITY_THRESHOLD:
            return ""
        return pdq_hash

    @staticmethod
    def get_examples() -> t.List[str]:
        return [
            # pdq/data/bridge-mods
            "f8f8f0cee0f4a84f06370a22038f63f0b36e2ed596621e1d33e6b39c4e9c9b22",
            "f8f8f0cee0f4a84f06370a2a038f63f0b36e26d596621e1d33e6b39c4e9c9b22",
            "f8f8f0cee0f4a84f0637022a038f67f0b36e26d596621e1d33e6b39c4e9c9b22",
            "f8f8f0cee0f4a84f06370a2a068f67f0b36e26d596621e1d33e6339c4e9c9b22",
            "f8f8f0cee0f4a84f06370a22038f67f0b36e2ed596221e1d33e6b39c4e9c9b22",
            "f8f8f0cee0f4a84f0e370a22038f67f0b36e2ed596221e1d33e6b39c4a9c9b22",
            "d8f8f0cec0f4a84f8e370a22038f67f0b36a2ed597231e1d72e6b39c4a9c9b22",
            "f8f8f0cee0f4a84f06370a22038f67f0b36e2ed596621e1d33e6339c4e9c9b22",
            "d0f8f1ccc0f4a84d0a370a3a228f67f0b36e2ed5b6623e1d33e6339c4e9c9b22",
            "d8f8f1eec0f4a84f0e37022a078f63f0b36e2ed596621e1d33e6239c4e9c9b22",
            "d8f8f0cec4f4a84f0637022a078f67f0b36e2ee5b6621e1d33e6239c4e9c9b22",
            "d8f8f0cec0f4a84f0637022a278f67f0b36e2ed596621e1d33e6339c4e9c9b22",
            # pdq/data/misc-images
            "e64cc9d91c623882f8d1f1d9a398e78c9f199b3bd83924f2b7e11e0bf861b064",
            "6227401f601ff4ccafcc9fad4b0d95d371a2eb7265a3285234d228ca94deeb2d",
            # Github invertocat - https://github.com/logos
            "c186f9619659658c4b6916daf934496985f4259c72c39676ab9edb631c3c349c",
            # Github octocat - https://github.com/logos
            "62c9789627838f69f23cf98c29e37836d61c87c31c59587c4b49a783f496725c",
        ]
