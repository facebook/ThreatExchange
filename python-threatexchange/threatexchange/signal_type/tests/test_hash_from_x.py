# Copyright (c) Meta Platforms, Inc. and affiliates.

import pytest
from threatexchange.signal_type import (
    md5,
    raw_text,
    trend_query,
    url_md5,
    url,
)
from threatexchange.signal_type.pdq import signal
from threatexchange.signal_type.signal_base import TextHasher
import typing as t


SIGNAL_TYPES_TO_TEST = [
    md5.VideoMD5Signal,
    signal.PdqSignal,
    raw_text.RawTextSignal,
    trend_query.TrendQuerySignal,
    url_md5.UrlMD5Signal,
    url.URLSignal,
]


def test_signal_names_unique():
    """
    Verify uniqueness of signal type names across all signal types.
    """
    seen: dict[str, t.Any] = {}
    for signal_type in SIGNAL_TYPES_TO_TEST:
        name = signal_type.get_name()
        assert (
            name not in seen
        ), f"Two signal types share the same name: {signal_type!r} and {seen[name]}"
        seen[name] = signal_type


@pytest.mark.parametrize("signal_type", SIGNAL_TYPES_TO_TEST)
def test_signal_types_have_content(signal_type):
    """
    Ensure that each signal type has associated content types.
    """
    assert signal_type.get_content_types(), f"{signal_type!r} has no content types"


@pytest.mark.parametrize(
    "signal_type", [s for s in SIGNAL_TYPES_TO_TEST if isinstance(s, TextHasher)]
)
def test_str_hashers_have_impl(signal_type):
    """
    Check that each TextHasher has an implementation that produces output.
    """
    assert signal_type.hash_from_str(
        "test string"
    ), f"{signal_type!r} produced no output from hasher"
