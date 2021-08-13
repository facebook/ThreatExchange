# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Mappings from threatexchange types to hmalib types or vice-versa. Must only have
constants.

python-threatxchange defines types for content, signal and indexes. However,
hmalib sometimes extends these types. Eg. We extend Indexes to provide S3
storage. In those cases, the mapping in python-threatexchange is out-of-date and
we must provide a mapping in hmalib land.

If you find yourself needing a map between hmalib types or hmalib and
python-threatexchange types, they should go here.

If you find yourself needing a map between python-threatexchange types alone,
they should go into python-threatexchange. eg. threatexchange.content_type.meta. 
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
