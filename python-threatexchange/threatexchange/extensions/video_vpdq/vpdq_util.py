# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import vpdq
import json
from json import JSONEncoder
import typing as t
import pathlib
from dataclasses import dataclass

QUALITY = "quality"
HASH = "hash"
TIMESTAMP = "timestamp"


@dataclass
class VPDQMatchResult:
    target_match_percent: float
    query_match_percent: float

    def __init__(self, target_match_percent: float = 0, query_match_percent: float = 0):
        self.target_match_percent = target_match_percent
        self.query_match_percent = query_match_percent


def vpdq_to_json(vpdq_features: t.List[vpdq.VpdqFeature]) -> str:
    """Convert from VPDQ features to json object and return the json object as a str"""
    data: t.Dict[str, t.Dict] = {}
    for feature in vpdq_features:
        frame_number = feature.frame_number
        data[frame_number] = {}
        data[frame_number][QUALITY] = feature.quality
        data[frame_number][HASH] = feature.hash
        # VPDQ feature's timestamp is round to 3 decimals
        data[frame_number][TIMESTAMP] = round(feature.timestamp, 3)
    return json.dumps(data)


def json_to_vpdq(json_str: str) -> t.List[vpdq.VpdqFeature]:
    """Load a str as a json object and convert from json object to VPDQ features"""
    features = []
    # VPDQ feature's timestamp is round to 3 decimals
    vpdq_json = json.loads(json_str, parse_float=lambda x: round(float(x), 3))
    for frame_number in vpdq_json:
        feature = vpdq_json[frame_number]
        features.append(
            vpdq.VpdqFeature(
                feature[QUALITY], frame_number, feature[HASH], feature[TIMESTAMP]
            )
        )
    return features


def dedupe(hashes: t.List[vpdq.VpdqFeature]) -> t.List[vpdq.VpdqFeature]:
    """Filter out the VPDQ feature with exact same hash in a list of VPDQ features

    Args:
        hashes

    Returns:
        list of VPDQ feature: List of VPDQeatures with unique hashes
    """
    unique_hashes = set()
    ret = []
    for h in hashes:
        if h.hex not in unique_hashes:
            ret.append(h)
            unique_hashes.add(h.hex)
    return ret


def quality_filter(
    hashes: t.List[vpdq.VpdqFeature], quality_tolerance: int
) -> t.List[vpdq.VpdqFeature]:
    """Filter VPDQ feature that has a quality lower than quality_tolerance

    Args:
        hashes
        distance_tolerance : If frames is this quality level then it will be ignored

    Returns:
        List of VPDQFeatures with quality higher than distance_tolerance
    """
    return list(filter(lambda hash: hash.quality >= quality_tolerance, hashes))


def read_file_to_hash(
    input_hash_filename: t.Union[str, pathlib.Path]
) -> t.List[vpdq.VpdqFeature]:
    """Read hash file and return vpdq hash

    Args:
        input_hash_filename : Input hash file path

    Returns:
        vpdq hash from the hash file"""

    hash = []
    with open(input_hash_filename, "r") as file:
        for line in file.readlines():
            line = line.strip()
            content = line.split(",")
            pdq_hash = vpdq.str_to_hash(content[2])
            feature = vpdq.VpdqFeature(
                int(content[1]), int(content[0]), pdq_hash, float(content[3])
            )
            hash.append(feature)

    return hash
