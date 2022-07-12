# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the vpdq signal type.
"""

import vpdq # type: ignore
from .vpdq_util import json_to_vpdq, vpdq_to_json
from .vpdq_brute_hasher import match_VPDQ_hash_brute
import pathlib
import typing as t
from threatexchange.content_type.content_base import ContentType
from threatexchange.content_type.video import VideoContent
import re
from threatexchange.signal_type import signal_base


class VideoVPDQSignal(signal_base.SimpleSignalType, signal_base.TextHasher):
    """
    Simple signal type for video using VPDQ.
    Read about VPDQ at https://github.com/facebook/ThreatExchange/tree/main/vpdq
    """

    INDICATOR_TYPE = "HASH_VIDEO_VPDQ"
    VPDQ_CONFIDENT_DISTANCE_THRESHOLD = 31
    VPDQ_CONFIDENT_QUALITY_THRESHOLD = 50

    @classmethod
    def get_content_types(self) -> t.List[t.Type[ContentType]]:
        return [VideoContent]

    @classmethod
    def validate_signal_str(cls, signal_str: str) -> str:
        """VPDQ hex str contains 64 hexidecimal characters."""
        vpdq_hashes = json_to_vpdq(signal_str)
        for hash in vpdq_hashes:
            if not re.match("^[0-9a-f]{64}$", hash.hex):
                raise ValueError("invalid VPDQ hash")
            if hash.quality < 0 or hash.quality > 100:
                raise ValueError("invalid VPDQ hash")
            if hash.frame_number < 0:
                raise ValueError("invalid VPDQ hash")
        return signal_str

    @classmethod
    def hash_from_file(cls, path: pathlib.Path) -> str:
        vpdq_hashes = vpdq.computeHash(str(path))
        return vpdq_to_json(vpdq_hashes)

    @classmethod
    def hash_from_str(cls, path: str) -> str:
        vpdq_hashes = vpdq.computeHash(path.rstrip())
        return vpdq_to_json(vpdq_hashes)

    @classmethod
    def compare_hash(
        cls, hash1: str, hash2: str, distance_threshold: t.Optional[int] = None
    ) -> signal_base.HashComparisonResult:
        vpdq_hash1 = json_to_vpdq(hash1)
        vpdq_hash2 = json_to_vpdq(hash2)
        if distance_threshold is None:
            distance_threshold = cls.VPDQ_CONFIDENT_QUALITY_THRESHOLD
        match_percent = match_VPDQ_hash_brute(
            vpdq_hash1,
            vpdq_hash2,
            distance_threshold,
            cls.VPDQ_CONFIDENT_QUALITY_THRESHOLD,
        )
        return signal_base.HashComparisonResult(match_percent, distance_threshold) # type: ignore

    @staticmethod
    def get_examples() -> t.List[str]:
        return [
            "0,100,e271017837246aaccddea259648fb7d62f435c89d9e99b2497763e216c8d055c,0.000",
            "1,100,c0f11178372c6aaccddea259648fbfd62f434c89c9e99b249772be216c8d055c,0.033",
            "2,100,c0f10b78372c6aacc5dea25b748fb7d22f434c89c9a9db249772b6216c8d855c,0.067",
            "3,100,c0f00b7837247aaccddea25b128fb7d22f434c894da9cb349776b621668dc55c,0.100",
            "4,100,c0700b78372e7aaccddea15b128f97c22f434c896da9cb349772f621668dc55c,0.133",
            "5,100,e03e0b1c372e7ea4c8dea35b1a8f97c22f4344896da9cb34df327221668dc55c,0.167",
            "6,100,e03e0b1c1f2efea4c8cea15b1acf97c2a743248965b94b34db327aa3628dc55c,0.200",
            "7,100,e03e0b9c1f0ebea4488eb55a5acf97c3a74324a965b949b459323aa3728de55c,0.233",
            "8,100,653e0b9e1f0ebe864886355a4acb93c38743a4a964b969b41d323ba3728df55e,0.267",
            "9,100,643c8f9e5f0eb6866886255a4a4bdbe38343b4e924b969b41d321ba33a85f55e,0.300",
            "10,100,74398d9e5f0eb626ea8635426a495be3c343b2e9b4b928b40db21ba33a85d55e,0.333",
            "11,100,70b9a59e4b8ff726ea963446286b4be3c363d269b4b924b40db20f930aa5d556,0.367",
            "12,100,3239059e0b8f5726fe96b606a46a4beb4963d269f4b9a4b48db20f930aa5d556,0.400",
            "13,100,b03906b88b9b572efe969296a44a69e96963da69f239e4b48d928f930aa55556,0.433",
            "14,100,a93956b9899e538f5ec6da96b44220e96d637b697239e6dc859285930aa53556,0.467",
            "15,100,a93dd6a9899e538b5f46da96944625e96da379617229e2dcc59285930aa57556,0.500",
            "16,100,a93cd7a9859e6b8f5d46da96945225e86da339617239e2dcc792859302a57556,0.533",
            "17,100,a93ac3b9958e2b8f7dee5a96945226e83da33963723962dcc792871302a17556,0.567",
            "18,100,e15ac339958c2b9f6dee4a969256b6d09da33963703972fcc79a87520281b556,0.600",
            "19,100,c07acb7895882b9d6dcbca9692d6a6d29da33963f07972f9c39887520a81b556,0.633",
            "20,100,d032ca789588a79c6dcbc91e12b6aed69da3b923f079d2f98bb10f528a81b554,0.667",
        ]
