# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Any re-useable mappings from threatexchange types to hmalib types or vice-versa.
Must only have constants.
"""
import typing as t

from threatexchange.signal_type.pdq import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.signal_base import SignalType

from hmalib.indexers.s3_indexers import (
    S3BackedMD5Index,
    S3BackedPDQIndex,
    S3BackedInstrumentedIndexMixin,
)

# Maps from signal type → index to use for that signal type.
INDEX_MAPPING: t.Dict[t.Type[SignalType], t.Type[S3BackedInstrumentedIndexMixin]] = {
    PdqSignal: S3BackedPDQIndex,
    VideoMD5Signal: S3BackedMD5Index,
}
