# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import random
from functools import reduce
from threatexchange.signal_type.pdq.pdq_utils import PDQ_HEX_STR_LEN, BITS_IN_PDQ


def get_zero_hash() -> str:
    """Return a pdq hash hex str that is zero for every byte"""
    return "0" * PDQ_HEX_STR_LEN


def get_random_hash() -> str:
    """Return a random pdq hash hex str"""
    return f"{random.randrange(2**256):0{PDQ_HEX_STR_LEN}x}"


def get_similar_hash(pdq_hex: str, dist: int) -> str:
    """Return a pdq hash hex str with dist hamming distance away from pdq_hex"""
    if not (0 <= dist <= BITS_IN_PDQ):
        raise ValueError("Invalid distance value")
    order = random.sample(range(BITS_IN_PDQ), k=dist)
    pdq_int = reduce(lambda x, y: x ^ (1 << y), order, int(pdq_hex, 16))
    return f"{pdq_int:0{PDQ_HEX_STR_LEN}x}"
