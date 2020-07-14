##!/usr/bin/env python

"""
Wrapper around the video content type.
"""
import typing as t

from ..signal_type import md5
from ..signal_type.base import SignalType
from .base import ContentType


class PhotoContent(ContentType):
    @classmethod
    def get_signal_types(cls) -> t.List[t.Type[SignalType]]:
        return [md5.PhotoMD5Signal]
