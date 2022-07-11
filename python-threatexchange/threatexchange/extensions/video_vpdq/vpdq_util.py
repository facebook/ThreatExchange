import vpdq
import json
from json import JSONEncoder

QUALITY = "quality"
HASH = "hash"
TIMESTAMP = "timestamp"


def vpdq_to_json(vpdq_features):
    data = {}
    for feature in vpdq_features:
        frame_number = feature.frame_number
        data[frame_number] = {}
        data[frame_number][QUALITY] = feature.quality
        data[frame_number][HASH] = feature.hash
        data[frame_number][TIMESTAMP] = feature.timestamp
    return json.dumps(data)


def json_to_vpdq(json_str):
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


def dedupe(hashes):
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


def quality_filter(hashes, quality_tolerance):
    """Filter VPDQ feature that has a quality lower than quality_tolerance

    Args:
        hashes (list of VPDQ feature)
        distance_tolerance (int): If frames is this quality level then it will be ignored

    Returns:
        list of VPDQ feature: List of VPDQeatures with quality higher than distance_tolerance
    """
    return list(filter(lambda hash: hash.quality >= quality_tolerance, hashes))
