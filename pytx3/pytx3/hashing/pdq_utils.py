#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

BITS_IN_PDQ = 256


def simple_distance_binary(bin_a, bin_b):
    assert len(bin_a) == BITS_IN_PDQ
    assert len(bin_b) == BITS_IN_PDQ
    distance = 0
    for i in range(BITS_IN_PDQ):
        if bin_a[i] != bin_b[i]:
            distance += 1
    return distance


def simple_distance(hex_a, hex_b):
    return simple_distance_binary(hex_to_binary_str(hex_a), hex_to_binary_str(hex_b))


def hex_to_binary_str(pdq_hex):
    assert len(pdq_hex) == BITS_IN_PDQ / 4
    # padding to 4 bindigits each hexdigit
    result = "".join(bin(int(c, 16))[2:].zfill(4) for c in pdq_hex)
    assert len(result) == BITS_IN_PDQ
    return result


def pdq_match(pdq_hex_a: str, pdq_hex_b: str, threshold: int) -> bool:
    distance = simple_distance(pdq_hex_a, pdq_hex_b)
    return distance <= threshold
