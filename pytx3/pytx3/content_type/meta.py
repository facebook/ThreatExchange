#!/usr/bin/env python

"""
Stores all the content type implementations for lookup
"""

import typing as t

from . import content_base, text, video, photo
from ..signal_type import signal_base


def get_all_content_types() -> t.List[t.Type[content_base.ContentType]]:
    """Returns all content_type implementations for commands"""
    return [text.TextContent, video.VideoContent, photo.PhotoContent]


def get_all_signal_types() -> t.Set[t.Type[signal_base.SignalType]]:
    """Returns all signal_type implementations for commands"""
    ret = set()
    return {s for c in get_all_content_types() for s in c.get_signal_types()}
