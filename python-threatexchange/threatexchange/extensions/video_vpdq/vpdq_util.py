import vpdq
import json
from json import JSONEncoder
import typing as t

QUALITY = "quality"
HASH = "hash"
TIMESTAMP = "timestamp"
TARGET_MATCH_PERCENT = "target_match_percent"
QUERY_MATCH_PERCENT = "query_match_percent"


def vpdq_to_json(vpdq_features: t.List[vpdq.VpdqFeature]) -> str:
    """Convert from VPDQ features to json object and return the json object as a str"""
    data = {}
    for feature in vpdq_features:
        frame_number = feature.frame_number
        data[frame_number] = {}
        data[frame_number][QUALITY] = feature.quality
        data[frame_number][HASH] = feature.hash
        data[frame_number][TIMESTAMP] = feature.timestamp
    return json.dumps(data)


def json_to_vpdq(json_str: str) -> t.List[vpdq.VpdqFeature]:
    """Load a str as a json object and convert from json object to VPDQ features"""
    features = []
    vpdq_json = json.loads(json_str)
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
        hashes (list of VPDQ feature)

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
        hashes (list of VPDQ feature)
        distance_tolerance (int): If frames is this quality level then it will be ignored

    Returns:
        list of VPDQ feature: List of VPDQeatures with quality higher than distance_tolerance
    """
    return list(filter(lambda hash: hash.quality >= quality_tolerance, hashes))