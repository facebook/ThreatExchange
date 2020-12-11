#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import pdqhash
import pathlib
import numpy as np
from PIL import Image, ImageOps


def pdq_from_file(path: pathlib.Path):
    """
    Given a path to a file return the PDQ Hash string in hex
    Current Supported file types: jpg
    """
    img_pil = Image.open(path)
    image = np.asarray(img_pil)
    hash_vector, quality = pdqhash.compute(image)

    bin_str = "".join([str(x) for x in hash_vector])

    # binary to hex using format string
    # '%0*' is for padding up to ceil(num_bits/4),
    # '%X' create a hex representation from the binary string's integer value
    hex_str = "%0*X" % ((len(bin_str) + 3) // 4, int(bin_str, 2))
    hex_str = hex_str.lower()

    return hex_str, quality
