#!/usr/bin/env python
# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Wrapper around the video content type.
"""
from PIL import Image
import io
import typing as t

from .content_base import ContentType, RotationType


class PhotoContent(ContentType):
    """
    Content that contains static visual imagery.

    Examples might be:
      * jpeg
      * png
      * gif (non-animated)
      * frames from videos
      * thumbnails of videos
    """

    @classmethod
    def rotate_image(cls, image_data: bytes, angle: float) -> bytes:
        """
        Rotate an image by a given angle.
        """
        with Image.open(io.BytesIO(image_data)) as img:
            rotated_img = img.rotate(angle, expand=True)
            with io.BytesIO() as buffer:
                rotated_img.save(buffer, format=img.format)
                return buffer.getvalue()

    @classmethod
    def flip_x(cls, image_data: bytes) -> bytes:
        """
        Flip the image horizontally along the X-axis.
        """
        with Image.open(io.BytesIO(image_data)) as img:
            flipped_img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            with io.BytesIO() as buffer:
                flipped_img.save(buffer, format=img.format)
                return buffer.getvalue()

    @classmethod
    def flip_y(cls, image_data: bytes) -> bytes:
        """
        Flip the image vertically along the Y-axis.
        """
        with Image.open(io.BytesIO(image_data)) as img:
            flipped_img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            with io.BytesIO() as buffer:
                flipped_img.save(buffer, format=img.format)
                return buffer.getvalue()

    @classmethod
    def flip_plus1(cls, image_data: bytes) -> bytes:
        """
        Flip the image diagonally along the line y = x.
        """
        with Image.open(io.BytesIO(image_data)) as img:
            flipped_img = img.transpose(Image.Transpose.ROTATE_270).transpose(
                Image.Transpose.FLIP_LEFT_RIGHT
            )
            with io.BytesIO() as buffer:
                flipped_img.save(buffer, format=img.format)
                return buffer.getvalue()

    @classmethod
    def flip_minus1(cls, image_data: bytes) -> bytes:
        """
        Flip the image diagonally along the line y = -x.
        """
        with Image.open(io.BytesIO(image_data)) as img:
            flipped_img = img.transpose(Image.Transpose.ROTATE_90).transpose(
                Image.Transpose.FLIP_LEFT_RIGHT
            )
            with io.BytesIO() as buffer:
                flipped_img.save(buffer, format=img.format)
                return buffer.getvalue()

    @classmethod
    def all_simple_rotations(cls, image_data: bytes) -> t.Dict[RotationType, bytes]:
        """
        Generate the 8 naive rotations of an image.

        This can be helpful for testing.
        And for image algorithms that don't have a native way to generate rotations during hashing,
        this can be a way to brute force rotations.
        """
        rotations = {
            RotationType.ORIGINAL: image_data,
            RotationType.ROTATE90: cls.rotate_image(image_data, 90),
            RotationType.ROTATE180: cls.rotate_image(image_data, 180),
            RotationType.ROTATE270: cls.rotate_image(image_data, 270),
            RotationType.FLIPX: cls.flip_x(image_data),
            RotationType.FLIPY: cls.flip_y(image_data),
            RotationType.FLIPPLUS1: cls.flip_plus1(image_data),
            RotationType.FLIPMINUS1: cls.flip_minus1(image_data),
        }
        return rotations
