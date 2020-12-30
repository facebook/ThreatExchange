#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Util file for Optical character recognition (OCR) related functions.
Use of pytesseract requires additional libaries already be installed, see https://github.com/madmaze/pytesseract#installation
"""

import pdqhash
import pathlib
import pytesseract
from PIL import Image, ImageOps


def text_from_image_file(path: pathlib.Path):
    """
    Given a path to a file return predicted OCR text
    Current Supported file types: jpg
    """
    img_pil = Image.open(path)
    return pytesseract.image_to_string(img_pil)
