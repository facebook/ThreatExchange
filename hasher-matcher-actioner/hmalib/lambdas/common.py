# Copyright (c) Meta Platforms, Inc. and affiliates.

import functools

from hmalib.common.mappings import (
    HMASignalTypeMapping,
    get_pytx_functionality_mapping,
)


@functools.lru_cache(maxsize=None)
def get_signal_type_mapping() -> HMASignalTypeMapping:
    """
    Cache-get signalTypeMapping. Call only if HMAConfig has been initialized.
    """
    return get_pytx_functionality_mapping().signal_and_content
