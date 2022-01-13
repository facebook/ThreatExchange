#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the video content type.
"""
import typing as t

from threatexchange.content_type.content_base import ContentType


class VideoContent(ContentType):
    """
    Content representing a sequence of images, giving the illusion of motion.

    Examples might be:
    * mp4
    * avi
    * gif animations
    """
