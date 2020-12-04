#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrapper around the video content type.
"""
import typing as t

from ..signal_type import raw_text, trend_query, url, md5, video_tmk_pdqf
from ..signal_type.signal_base import SignalType
from .content_base import ContentType


class VideoContent(ContentType):
    """
    Content representing a sequence of images, giving the illusion of motion.

    Examples might be:
    * mp4
    * avi
    * gif animations
    """

    @classmethod
    def get_signal_types(cls) -> t.List[t.Type[SignalType]]:
        return [md5.VideoMD5Signal, video_tmk_pdqf.VideoTmkPdqfSignal]
