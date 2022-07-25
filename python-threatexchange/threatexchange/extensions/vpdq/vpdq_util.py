# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import vpdq
import json
from json import JSONEncoder
import typing as t
import pathlib
from dataclasses import dataclass
from threatexchange.hashing.pdq_utils import get_random_hash

QUALITY = "quality"
HASH = "hash"
TIMESTAMP = "timestamp"
VPDQ_TIMESTAMP_PRECISION = 3
VPDQ_QUALITY_THRESHOLD = 50
VPDQ_DISTANCE_THRESHOLD = 31


@dataclass
class VPDQMatchResult:
    """Data class for VPDQ match result"""

    query_match_percent: float = 0.0
    compared_match_percent: float = 0.0


def vpdq_to_json(vpdq_features: t.List[vpdq.VpdqFeature]) -> str:
    """Convert from VPDQ features to json object and return the json object as a str"""
    data: t.Dict[str, t.Dict] = {}
    for feature in vpdq_features:
        frame_number = feature.frame_number
        data[frame_number] = {}
        data[frame_number][QUALITY] = feature.quality
        data[frame_number][HASH] = feature.hash
        # VPDQ feature's timestamp is round to 3 decimals
        data[frame_number][TIMESTAMP] = round(
            feature.timestamp, VPDQ_TIMESTAMP_PRECISION
        )
    return json.dumps(data)


def json_to_vpdq(json_str: str) -> t.List[vpdq.VpdqFeature]:
    """Load a str as a json object and convert from json object to VPDQ features"""
    features = []
    # VPDQ feature's timestamp is round to 3 decimals
    vpdq_json = json.loads(
        json_str, parse_float=lambda x: round(float(x), VPDQ_TIMESTAMP_PRECISION)
    )
    for frame_number, feature in vpdq_json.items():
        features.append(
            vpdq.VpdqFeature(
                feature[QUALITY], frame_number, feature[HASH], feature[TIMESTAMP]
            )
        )
    return features


def dedupe(features: t.List[vpdq.VpdqFeature]) -> t.List[vpdq.VpdqFeature]:
    """Filter out the VPDQ feature with exact same hash in a list of VPDQ features

    Args:
        features

    Returns:
        List of VPDQ Features with unique features
    """
    unique_features = set()
    ret = []
    for h in features:
        if h.hex not in unique_features:
            ret.append(h)
            unique_features.add(h.hex)
    return ret


def quality_filter(
    features: t.List[vpdq.VpdqFeature], quality_tolerance: int
) -> t.List[vpdq.VpdqFeature]:
    """Filter VPDQ feature that has a quality lower than quality_tolerance

    Args:
        features
        quality_tolerance : If frames is this quality level then it will be ignored

    Returns:
        List of VPDQFeatures with quality higher than quality_tolerance
    """
    return [f for f in features if f.quality >= quality_tolerance]


def read_file_to_hash(
    input_hash_filename: t.Union[str, pathlib.Path]
) -> t.List[vpdq.VpdqFeature]:
    """Read hash file and return list of VPDQ features

    Args:
        Input hash file path

    Returns:
        VPDQ features from the hash file"""

    with open(input_hash_filename, "r") as file:
        return json_to_vpdq(file.read())


def dump_hash_to_file(
    output_hash_filename: t.Union[str, pathlib.Path],
    vpdq_features: t.List[vpdq.VpdqFeature],
) -> None:
    """Write list of VPDQ features to output hash file

    Args:
        Output hash file path
        VPDQ features write to the output file"""
    with open(output_hash_filename, "w") as file:
        file.write(vpdq_to_json(vpdq_features))


def prepare_vpdq_feature(
    signal_str: str, quality_tolerance: int
) -> t.List[vpdq.VpdqFeature]:
    """Convert signal_str to deduped and quality-filtered vdqp features

    Args:
    quality_tolerance : The quality tolerance of VPDQ Feature.
    If VPDQ Feature is below this quality level then it will not be added
    """

    features = json_to_vpdq(signal_str)
    return dedupe(quality_filter(features, quality_tolerance))


def get_random_VPDQs(
    frame_count: int, seconds_per_frame: float = 1.0, quality: int = 100
) -> t.List[vpdq.VpdqFeature]:
    """Return a List which contains frame_count random VPDQ features with same quality and each feature's time stamp differs by seconds_per_frame"""
    return [
        vpdq.VpdqFeature(
            quality, i, vpdq.str_to_hash(get_random_hash()), i * seconds_per_frame
        )
        for i in range(frame_count)
    ]


def pdq_hashes_to_VPDQ_features(
    pdq_hashes: t.List[str], seconds_per_frame: float = 1.0, quality: int = 100
) -> t.List[vpdq.VpdqFeature]:
    """Return a List of VPDQ features generated from pdq_hashes with same quality and each feature's time stamp differs by seconds_per_frame"""
    return [
        vpdq.VpdqFeature(
            quality, i, vpdq.str_to_hash(pdq_hashes[i]), i * seconds_per_frame
        )
        for i in range(len(pdq_hashes))
    ]
