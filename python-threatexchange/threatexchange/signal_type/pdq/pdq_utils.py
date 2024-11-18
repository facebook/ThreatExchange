#!/usr/bin/env python
# Copyright (c) Meta Platforms, Inc. and affiliates.

import numpy as np
import typing as t

BITS_IN_PDQ = 256
PDQ_HEX_STR_LEN = int(BITS_IN_PDQ / 4)


def simple_distance_binary(bin_a: str, bin_b: str) -> int:
    """
    Returns the hamming distance of two binary strings.
    """
    assert len(bin_a) == BITS_IN_PDQ
    assert len(bin_b) == BITS_IN_PDQ
    return sum(bin_a[i] != bin_b[i] for i in range(BITS_IN_PDQ))


def simple_distance(hex_a: str, hex_b: str) -> int:
    """
    Returns the binary hamming distance of two hexadecimal strings.
    """
    return simple_distance_binary(hex_to_binary_str(hex_a), hex_to_binary_str(hex_b))


def hex_to_binary_str(pdq_hex: str) -> str:
    """
    Convert a hexadecimal string to a binary string. Requires input string to be length PDQ_HEX_STR_LEN.
    """
    assert len(pdq_hex) == PDQ_HEX_STR_LEN
    # padding to 4 bindigits each hexdigit
    result = "".join(bin(int(c, 16))[2:].zfill(4) for c in pdq_hex)
    assert len(result) == BITS_IN_PDQ
    return result


def binary_str_to_hex(pdq_binary: str) -> str:
    """
    Convert a binary string to a hexadecimal string. Requires input string to be length BITS_IN_PDQ.
    """
    assert len(pdq_binary) == BITS_IN_PDQ
    # [2:] ignores the 0x at the begining of the hex_str
    result = hex(int(pdq_binary, 2))[2:].zfill(PDQ_HEX_STR_LEN)
    assert len(result) == PDQ_HEX_STR_LEN
    return result


def pdq_match(pdq_hex_a: str, pdq_hex_b: str, threshold: int) -> bool:
    """
    Returns true if hamming distance of two hex strings are within (<=) the given threshold.
    """
    distance = simple_distance(pdq_hex_a, pdq_hex_b)
    return distance <= threshold


def convert_pdq_strings_to_ndarray(pdq_strings: t.Sequence[str]) -> np.ndarray:
    """
    Convert multiple PDQ hash strings to a numpy array.
    """
    if not all(len(pdq_str) == PDQ_HEX_STR_LEN for pdq_str in pdq_strings):
        raise ValueError("All PDQ hash strings must be 64 hex characters long")

    binary_arrays = []
    for pdq_str in pdq_strings:
        hash_bytes = bytes.fromhex(pdq_str)
        binary_array = np.unpackbits(np.frombuffer(hash_bytes, dtype=np.uint8))
        binary_arrays.append(binary_array)

    return np.array(binary_arrays, dtype=np.uint8)
