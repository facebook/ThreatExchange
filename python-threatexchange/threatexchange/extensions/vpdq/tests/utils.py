import random
import vpdq
import typing as t
from threatexchange.hashing.pdq_utils import hex_to_binary_str, BITS_IN_PDQ

# Hex -> 4 digits Binary
BITS_IN_PDQ_HEX = int(BITS_IN_PDQ / 4)


def get_zero_hash() -> str:
    """Return a pdq hash str that is zero for every byte"""
    return "".join("0" * BITS_IN_PDQ_HEX)


def get_random_hash() -> str:
    """Return random pdq hash"""
    return "".join(("%x" % random.randint(0, 15)) for i in range(BITS_IN_PDQ_HEX))


def get_similar_hash(signal_str: str, dist: int) -> str:
    order = list(range(BITS_IN_PDQ))
    random.shuffle(order)
    bin_list = list(hex_to_binary_str(signal_str))
    for i in order:
        if dist == 0:
            bin_str = "".join(bin_list)
            # [2:] ignores the 0x at the begining of the hex_str
            hex_str = hex(int(bin_str, 2))[2:].zfill(BITS_IN_PDQ_HEX)
            return hex_str
        bin_list[i] = str(int(bin_list[i]) ^ 1)
        dist -= 1
    raise ValueError("Not possible")


def get_random_VPDQs(
    video_length: int, seconds_per_hash: int = 1.0, quality: int = 100
) -> t.List[vpdq.VpdqFeature]:
    ret: t.List[vpdq.VpdqFeature] = []
    timestamp = 0.0
    for i in range(video_length):
        feature = vpdq.VpdqFeature(
            quality, i, vpdq.str_to_hash(get_random_hash), timestamp
        )
        timestamp += seconds_per_hash
        ret.append(feature)
