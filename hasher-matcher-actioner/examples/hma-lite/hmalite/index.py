# Copyright (c) Meta Platforms, Inc. and affiliates.

from hmalite.config import HmaLiteConfig
from threatexchange.signal_type import pdq_index


####################### INDEX HACKS #######################
# This doesn't really behave the way you might think -
# instances of flask are destroyed and created all the time/thread
# local-d, so you'll get a bunch of copies of this(?)
# Someday we'll have to figure out the correct way to stage it
_INDEX = None


def get_local_index():
    global _INDEX
    if not _INDEX:
        config = HmaLiteConfig.from_flask_current_app()
        with open(config.local_index_file, "rb") as f:
            index = pdq_index.PDQIndex.deserialize(f.read())
        _INDEX = index
    return _INDEX


def reset_index(index):
    global _INDEX
    _INDEX = index
