# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import random
from threatexchange.hashing.pdq_utils import *

def get_zero_hash() -> str:
    """Return a pdq hash hex str that is zero for every byte"""
    return "0" * PDQ_HEX_STR_LEN


def get_random_hash() -> str:
    """Return a random pdq hash hex str"""
    return f"{random.randrange(2**256):0{PDQ_HEX_STR_LEN}x}"


def get_similar_hash(pdq_hex: str, dist: int) -> str:
    """Return a pdq hash hex str with dist hamming distance away from pdq_hex"""
    if dist > BITS_IN_PDQ or dist < 0:
        raise ValueError("Invalid distance value")
    order = random.sample(range(BITS_IN_PDQ), k=dist)
    bin_list = list(hex_to_binary_str(pdq_hex))
    for i in order:
        bin_list[i] = str(int(bin_list[i]) ^ 1)
    bin_str = "".join(bin_list)
    return binary_str_to_hex(bin_str)