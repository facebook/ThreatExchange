# Copyright (c) Meta Platforms, Inc. and affiliates.

import io
import pdqhash
import pathlib
import numpy as np
from PIL import Image
import typing as t


PDQOutput = t.Tuple[
    str, int
]  # hexadecimal representation of the Hash vector and a numerical quality value


def pdq_from_file(path: pathlib.Path) -> PDQOutput:
    """
    Given a path to a file return the PDQ Hash string in hex.
    Current tested against: jpg
    """
    np_array = _convert_image_to_correct_array_dimension(Image.open(path))
    return _pdq_from_numpy_array(np_array)


def pdq_from_bytes(file_bytes: bytes) -> PDQOutput:
    """
    For the bytestream from an image file, compute PDQ Hash and quality.
    """
    np_array = _convert_image_to_correct_array_dimension(
        Image.open(io.BytesIO(file_bytes))
    )
    return _pdq_from_numpy_array(np_array)


def _pdq_from_numpy_array(array: np.ndarray) -> PDQOutput:
    hash_vector, quality = pdqhash.compute(array)

    bin_str = "".join([str(x) for x in hash_vector])

    # binary to hex using format string
    # '%0*' is for padding up to ceil(num_bits/4),
    # '%X' create a hex representation from the binary string's integer value
    hex_str = "%0*X" % ((len(bin_str) + 3) // 4, int(bin_str, 2))
    hex_str = hex_str.lower()

    return hex_str, quality


def _convert_image_to_correct_array_dimension(image: Image) -> np.ndarray:
    """
    Handle possible image format conversion or
    """
    if image.mode == "LA":
        # LA images (luminance with alpha) return 3 dimensional ndarray
        # which is incompatible with pdqhash
        image = image.convert("RGB")

    array = np.asarray(image)

    # Convert possible 2D array to 3D array
    # This is more efficient than converting to RGB for mode L images.
    if array.ndim == 2:
        array = np.concatenate([array[..., np.newaxis]] * 3, axis=2)

    return array
