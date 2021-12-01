#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Abstraction for different content types.

This records all the valid signal types for a piece of content.
"""

import typing as t

from .. import common
from ..signal_type import signal_base, raw_text, trend_query, url


class ContentType:
    @classmethod
    def get_name(cls) -> str:
        """The human-friendly display name"""
        return common.class_name_to_human_name(cls.__name__, "Content")

    @classmethod
    def get_signal_types(cls) -> t.List[t.Type[signal_base.SignalType]]:
        raise NotImplementedError
