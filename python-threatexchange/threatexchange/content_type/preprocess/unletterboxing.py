#!/usr/bin/env python
# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t

from PIL import Image


def _flattened_pixels(image: Image.Image) -> t.Sequence[t.Any]:
    """
    Pixel values of the image as a flat sequence.

    `get_flattened_data` needs Pillow>=12.1, which requires Python>=3.10;
    older Pillows only have `getdata` (deprecated in 12.1).
    """
    img: t.Any = image
    if hasattr(img, "get_flattened_data"):
        return img.get_flattened_data()
    return img.getdata()


def is_pixel_black(pixel: tuple, black_threshold: int):
    """
    Check if each color channel in the pixel is below the threshold
    """
    r, g, b = pixel
    return r <= black_threshold and g <= black_threshold and b <= black_threshold


def detect_top_border(image: Image.Image, black_threshold: int = 0) -> int:
    """
    Detect the top black border by counting rows with only black pixels.
    Checks each RGB channel of each pixel in each row.
    Returns the first row that is not all black from the top.
    """
    width, height = image.size
    for y in range(height):
        row_pixels = list(_flattened_pixels(image.crop((0, y, width, y + 1))))
        if all(
            is_pixel_black(t.cast(t.Tuple[t.Any, ...], pixel), black_threshold)
            for pixel in row_pixels
        ):
            continue
        return y
    return height


def detect_bottom_border(image: Image.Image, black_threshold: int = 0) -> int:
    """
    Detect the bottom black border by counting rows with only black pixels from the bottom up.
    Checks each RGB channel of each pixel in each row.
    Returns the first row that is not all black from the bottom.
    """
    width, height = image.size
    for y in range(height - 1, -1, -1):
        row_pixels = list(_flattened_pixels(image.crop((0, y, width, y + 1))))
        if all(
            is_pixel_black(t.cast(t.Tuple[t.Any, ...], pixel), black_threshold)
            for pixel in row_pixels
        ):
            continue
        return height - y - 1
    return height


def detect_left_border(image: Image.Image, black_threshold: int = 0) -> int:
    """
    Detect the left black border by counting columns with only black pixels.
    Checks each RGB channel of each pixel in each column.
    Returns the first column from the left that is not all black.
    """
    width, height = image.size
    for x in range(width):
        col_pixels = list(_flattened_pixels(image.crop((x, 0, x + 1, height))))
        if all(
            is_pixel_black(t.cast(t.Tuple[t.Any, ...], pixel), black_threshold)
            for pixel in col_pixels
        ):
            continue
        return x
    return width


def detect_right_border(image: Image.Image, black_threshold: int = 0) -> int:
    """
    Detect the right black border by counting columns with only black pixels from the right.
    Checks each RGB channel of each pixel in each column.
    Returns the first column from the right that is not all black.
    """
    width, height = image.size
    for x in range(width - 1, -1, -1):
        col_pixels = list(_flattened_pixels(image.crop((x, 0, x + 1, height))))
        if all(
            is_pixel_black(t.cast(t.Tuple[t.Any, ...], pixel), black_threshold)
            for pixel in col_pixels
        ):
            continue
        return width - x - 1
    return width
