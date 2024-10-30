#!/usr/bin/env python
# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Abstraction for different content types.

This records all the valid signal types for a piece of content.
"""

from enum import StrEnum, auto
import typing as t

from threatexchange import common


class ContentType:
    @classmethod
    def get_name(cls) -> str:
        """The human-friendly display name"""
        return common.class_name_to_human_name(cls.__name__, "Content")

    @classmethod
    def extract_additional_content(
        cls, content_arg: str
    ) -> t.List[t.Tuple[t.Type["ContentType"], str]]:
        """
        Post-process/download content to find additional components

        Examples might be:
        * URL => download page content and return photo/video/text/URL snippets
        * File => Identify content based on file type and return appropriate snippets
        * Photo => run OCR and extract text
        * Video => break out photo thumbnail, close caption text, audio
        """
        return []


class RotationType(StrEnum):
    """
    Enum for 8 simple rotations of an image.
    Used to store all generated rotations of an image,
    whose algorithms don't have a native way to generate rotations during hashing.
    """

    ORIGINAL = auto()  # No rotation; the object is in its original orientation
    ROTATE90 = auto()  # Rotates the object 90 degrees
    ROTATE180 = auto()  # Rotates the object 180 degrees (half-turn)
    ROTATE270 = auto()  # Rotates the object 270 degrees
    FLIPX = auto()  # Flip the object horizontally along the X-axis
    FLIPY = auto()  # Flip the object horizontally along the Y-axis
    FLIPPLUS1 = auto()  # Diagonal flip along the line y = x
    FLIPMINUS1 = auto()  # Diagonal flip along the line y = -x
