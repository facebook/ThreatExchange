#!/usr/bin/env python
# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Abstraction for different content types.

This records all the valid signal types for a piece of content.
"""

from enum import Enum, auto
import typing as t

import common


class ContentType:
    @classmethod
    def get_name(cls) -> str:
        """The human-friendly display name"""
        return common.class_name_to_human_name(cls.__name__, "Content")

    @classmethod
    def extract_additional_content(
        cls, content_in_file: Path, available_content: t.Sequence[t.Type["ContentType"]]
    ) -> t.Dict[t.Type["ContentType"], t.List[Path]]:
        """
        Post-process/download content to find additional components

        Examples might be:
        * URL => download page content and return photo/video/text/URL snippets
        * File => Identify content based on file type and return appropriate snippets
        * Photo => run OCR and extract text
        * Video => break out photo thumbnail, close caption text, audio
        """
        return {}


class RotationType(Enum):
    """
    Enum for 8 simple rotations of an image.
    Used to store all generated rotations of an image,
    whose algorithms don't have a native way to generate rotations during hashing.
    """

    ORIGINAL = "original"  # No rotation; the object is in its original orientation
    ROTATE90 = "rotate90"  # Rotates the object 90 degrees
    ROTATE180 = "rotate180"  # Rotates the object 180 degrees (half-turn)
    ROTATE270 = "rotate270"  # Rotates the object 270 degrees
    FLIPX = "flipx"  # Flip the object horizontally along the X-axis
    FLIPY = "flipy"  # Flip the object horizontally along the Y-axis
    FLIPPLUS1 = "flipplus1"  # Diagonal flip along the line y = x
    FLIPMINUS1 = "flipminus1"  # Diagonal flip along the line y = -x
