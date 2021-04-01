#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Util file for Optical character recognition (OCR) related functions.
Use of pytesseract requires additional libaries already be installed, see https://github.com/madmaze/pytesseract#installation
"""

import pathlib
import pytesseract
import warnings
from PIL import Image


def text_from_image_file(path: pathlib.Path):
    """
    Given a path to a file return predicted OCR text
    Current tested against: jpg
    """
    img_pil = Image.open(path)
    try:
        return pytesseract.image_to_string(img_pil)
    except pytesseract.TesseractNotFoundError as e:
        warnings.warn(
            str(e),
            category=UserWarning,
        )
    return ""
