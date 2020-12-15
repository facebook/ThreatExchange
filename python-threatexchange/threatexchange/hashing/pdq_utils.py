#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

BITS_IN_PDQ = 256


def simple_distance_binary(bin_a, bin_b):
    """
    Returns the hamming distance of two binary strings.
    """
    assert len(bin_a) == BITS_IN_PDQ
    assert len(bin_b) == BITS_IN_PDQ
    return sum(bin_a[i] != bin_b[i] for i in range(BITS_IN_PDQ))


def simple_distance(hex_a, hex_b):
    """
    Returns the binary hamming distance of two hexadecimal strings.
    """
    return simple_distance_binary(hex_to_binary_str(hex_a), hex_to_binary_str(hex_b))


def hex_to_binary_str(pdq_hex):
    """
    Convert a hexadecimal string to a binary string. Requires input string to be length BITS_IN_PDQ / 4.
    """
    assert len(pdq_hex) == BITS_IN_PDQ / 4
    # padding to 4 bindigits each hexdigit
    result = "".join(bin(int(c, 16))[2:].zfill(4) for c in pdq_hex)
    assert len(result) == BITS_IN_PDQ
    return result


def pdq_match(pdq_hex_a: str, pdq_hex_b: str, threshold: int) -> bool:
    """
    Returns true if hamming distance of two hex strings are within (<=) the given threshold.
    """
    distance = simple_distance(pdq_hex_a, pdq_hex_b)
    return distance <= threshold
