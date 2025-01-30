# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t
import pytest

from threatexchange.exchanges.clients.ncmec.tests.test_hash_api import (
    api,
    empty_api_response,
)
from threatexchange.exchanges.fetch_state import FetchDelta
from threatexchange.exchanges.impl.ncmec_api import (
    NCMECCollabConfig,
    NCMECSignalExchangeAPI,
    NCMECSignalMetadata,
)

from threatexchange.exchanges.clients.ncmec.hash_api import (
    NCMECEntryUpdate,
    NCMECEnvironment,
    NCMECHashAPI,
)

from threatexchange.signal_type.md5 import VideoMD5Signal


@pytest.fixture
def exchange(api: NCMECHashAPI, monkeypatch: pytest.MonkeyPatch):
    collab = NCMECCollabConfig(NCMECEnvironment.Industry, "Test")
    signal_exchange = NCMECSignalExchangeAPI(collab, "user", "pass")
    monkeypatch.setattr(signal_exchange, "get_client", lambda _environment: api)
    return signal_exchange


@pytest.fixture
def empty_exchange(empty_api_response: NCMECHashAPI, monkeypatch: pytest.MonkeyPatch):
    collab = NCMECCollabConfig(NCMECEnvironment.Industry, "Test")
    signal_exchange = NCMECSignalExchangeAPI(collab, "user", "pass")
    monkeypatch.setattr(
        signal_exchange, "get_client", lambda _environment: empty_api_response
    )
    return signal_exchange


def assert_delta(
    delta: FetchDelta,
    updates: set[str],
    progress_timestamp: int,
    is_stale: bool,
    get_entries_max_ts: int,
    paging_url: str,
) -> None:
    assert set(delta.updates) == updates
    assert len(delta.updates) == len(updates)
    assert delta.checkpoint.get_progress_timestamp() == progress_timestamp
    assert delta.checkpoint.is_stale() is is_stale
    assert delta.checkpoint.get_entries_max_ts == get_entries_max_ts
    assert delta.checkpoint.paging_url == paging_url


def test_fetch(exchange: NCMECSignalExchangeAPI, monkeypatch: pytest.MonkeyPatch):
    frozen_time = 1664496000
    monkeypatch.setattr("time.time", lambda: frozen_time)
    it = exchange.fetch_iter([], None)
    total_updates: t.Dict[str, NCMECEntryUpdate] = {}

    # Fetch 1
    delta = next(it, None)
    assert delta is not None
    exchange.naive_fetch_merge(total_updates, delta.updates)
    assert_delta(
        delta,
        {
            "42-image1",
            "43-image4",
            "42-video1",
            "42-video4",
        },
        0,
        False,
        0,
        "/v2/entries?from=2017-10-20T00%3A00%3A00.000Z&to=2017-10-30T00%3A00%3A00.000Z&start=2001&size=1000&max=3000",
    )

    # Fetch 2
    delta = next(it, None)
    assert delta is not None
    assert len(delta.updates) == 1
    exchange.naive_fetch_merge(total_updates, delta.updates)

    assert_delta(
        delta,
        {"42-image10"},
        0,
        False,
        0,
        "/v2/entries?from=2017-10-20T00%3A00%3A00.000Z&to=2017-10-30T00%3A00%3A00.000Z&start=3001&size=1000&max=4000",
    )

    # Fetch 3
    delta = next(it, None)
    assert len(delta.updates) == 2
    exchange.naive_fetch_merge(total_updates, delta.updates)
    assert_delta(
        delta,
        {"101-willupdate", "101-willdelete"},
        0,
        False,
        0,
        "/v2/entries?from=2017-10-20T00%3A00%3A00.000Z&to=2017-10-30T00%3A00%3A00.000Z&start=4001&size=1000&max=5000",
    )

    # Fetch 4
    delta = next(it, None)
    assert len(delta.updates) == 2
    exchange.naive_fetch_merge(total_updates, delta.updates)
    assert_delta(delta, {"101-willupdate", "101-willdelete"}, 0, False, 0, "")

    ## No more data, but one final checkpoint
    delta = next(it, None)
    assert len(delta.updates) == 0
    progress_timestamp = frozen_time - 5
    assert_delta(delta, set(), progress_timestamp, False, progress_timestamp, "")

    as_signals = NCMECSignalExchangeAPI.naive_convert_to_signal_type(
        [VideoMD5Signal], exchange.collab, total_updates
    )[VideoMD5Signal]
    assert as_signals == {
        "b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1": NCMECSignalMetadata({42: set()}),
        "facefacefacefacefacefacefaceface": NCMECSignalMetadata({101: {"A2"}}),
    }

    assert next(it, None) is None  # We fetched everything

    # Test esp_id filter
    collab = NCMECCollabConfig(NCMECEnvironment.Industry, "Test")
    collab.only_esp_ids = {101}
    as_signals = NCMECSignalExchangeAPI.naive_convert_to_signal_type(
        [VideoMD5Signal], collab, total_updates
    )[VideoMD5Signal]
    assert as_signals == {
        "facefacefacefacefacefacefaceface": NCMECSignalMetadata({101: {"A2"}}),
    }
    collab.only_esp_ids = {42}
    as_signals = NCMECSignalExchangeAPI.naive_convert_to_signal_type(
        [VideoMD5Signal], collab, total_updates
    )[VideoMD5Signal]
    assert as_signals == {
        "b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1": NCMECSignalMetadata({42: set()}),
    }
    collab.only_esp_ids = set()
    as_signals = NCMECSignalExchangeAPI.naive_convert_to_signal_type(
        [VideoMD5Signal], collab, total_updates
    )[VideoMD5Signal]
    assert as_signals == {
        "b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1": NCMECSignalMetadata({42: set()}),
        "facefacefacefacefacefacefaceface": NCMECSignalMetadata({101: {"A2"}}),
    }


def test_empty_fetch(
    empty_exchange: NCMECSignalExchangeAPI, monkeypatch: pytest.MonkeyPatch
):
    it = empty_exchange.fetch_iter([], None)
    # No updates
    delta = next(it, None)
    assert delta is not None
    assert len(delta.updates) == 0
    assert_delta(delta, set(), 0, False, 0, "")

    delta = next(it, None)
    assert delta is None  # We fetched everything
