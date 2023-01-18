# Copyright (c) Meta Platforms, Inc. and affiliates.

from threatexchange.content_type.photo import PhotoContent
from threatexchange.content_type.video import VideoContent
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.pdq import PdqSignal

from hmalib.common.mappings import HMASignalTypeMapping


def get_default_signal_type_mapping() -> HMASignalTypeMapping:
    return HMASignalTypeMapping(
        content_types=[PhotoContent, VideoContent],
        signal_types=[PdqSignal, VideoMD5Signal],
    )
