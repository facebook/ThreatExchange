#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import io
import pdqhash
import pathlib
import numpy
from PIL import Image, ImageOps
import typing as t


PDQOutput = t.Tuple[
    str, int
]  # hexadecimal representation of the Hash vector and a numerical quality value


def pdq_from_file(path: pathlib.Path) -> PDQOutput:
    """
    Given a path to a file return the PDQ Hash string in hex.
    Current tested against: jpg
    """
    img_pil = Image.open(path)
    image = numpy.asarray(img_pil)
    return _pdq_from_numpy_array(image)


def pdq_from_bytes(file_bytes: bytes) -> PDQOutput:
    """
    For the bytestream from an image file, compute PDQ Hash and quality.
    """
    np_array = numpy.asarray(Image.open(io.BytesIO(file_bytes)))
    return _pdq_from_numpy_array(np_array)


def _pdq_from_numpy_array(array: numpy.ndarray) -> PDQOutput:
    hash_vector, quality = pdqhash.compute(array)

    bin_str = "".join([str(x) for x in hash_vector])

    # binary to hex using format string
    # '%0*' is for padding up to ceil(num_bits/4),
    # '%X' create a hex representation from the binary string's integer value
    hex_str = "%0*X" % ((len(bin_str) + 3) // 4, int(bin_str, 2))
    hex_str = hex_str.lower()

    return hex_str, quality
