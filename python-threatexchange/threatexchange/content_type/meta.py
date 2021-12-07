#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Stores all the content type implementations for lookup
"""

import functools
import typing as t

from . import content_base, text, video, photo, pdf, url
from ..signal_type import signal_base


@functools.lru_cache(1)
def get_all_content_types() -> t.List[t.Type[content_base.ContentType]]:
    """Returns all content_type implementations for commands"""
    return [
        text.TextContent,
        video.VideoContent,
        photo.PhotoContent,
        pdf.PDFContent,
        url.URL,
    ]


@functools.lru_cache(1)
def get_content_types_by_name() -> t.Dict[str, t.Type[content_base.ContentType]]:
    return {c.get_name(): c for c in get_all_content_types()}


@functools.lru_cache(1)
def get_all_signal_types() -> t.Set[t.Type[signal_base.SignalType]]:
    """Returns all signal_type implementations for commands"""
    return {s for c in get_all_content_types() for s in c.get_signal_types()}


@functools.lru_cache(1)
def get_signal_types_by_name() -> t.Dict[str, t.Type[signal_base.SignalType]]:
    return {s.get_name(): s for s in get_all_signal_types()}


@functools.lru_cache(maxsize=None)
def _get_content_type_map():
    return {
        content_type.get_name(): content_type
        for content_type in get_all_content_types()
    }


def get_content_type_for_name(name: str) -> t.Type[content_base.ContentType]:
    """
    Given a name, get the ContentTYpe which returns that name on calling
    get_name().

    Note: Raises KeyError if not found.
    """
    return _get_content_type_map()[name]
