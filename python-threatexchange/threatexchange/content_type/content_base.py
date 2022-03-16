#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Abstraction for different content types.

This records all the valid signal types for a piece of content.
"""

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
