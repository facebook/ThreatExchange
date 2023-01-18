#!/usr/bin/env python
# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Wrapper around the video content type.
"""

from .content_base import ContentType


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
