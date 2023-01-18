# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t
import pytest

from threatexchange.exchanges.clients.ncmec.tests.test_hash_api import api
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


def test_fetch(exchange: NCMECSignalExchangeAPI, monkeypatch: pytest.MonkeyPatch):
    frozen_time = 1664496000
    monkeypatch.setattr("time.time", lambda: frozen_time)
    it = exchange.fetch_iter([], None)
    # Since our test data from test_hash_api is is all in one fetch sequence,
    # we'd have to craft some specialized data to get the NCMECSignalAPI split it
    # into multiple updates

    # Fetch 1
    delta = next(it, None)
    assert delta is not None
    assert len(delta.updates) == 7
    total_updates: t.Dict[str, NCMECEntryUpdate] = {}
    exchange.naive_fetch_merge(total_updates, delta.updates)

    assert delta.checkpoint.get_progress_timestamp() == frozen_time - 5
    assert delta.checkpoint.is_stale() is False
    assert delta.checkpoint.get_entries_max_ts == frozen_time - 5

    assert set(delta.updates) == {
        "43-image4",
        "42-image1",
        "42-video1",
        "42-video4",
        "42-image10",
        "101-willdelete",
        "101-willupdate",
    }

    as_signals = NCMECSignalExchangeAPI.naive_convert_to_signal_type(
        [VideoMD5Signal], exchange.collab, total_updates
    )[VideoMD5Signal]
    assert as_signals == {
        "b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1": NCMECSignalMetadata({42: set()}),
        "facefacefacefacefacefacefaceface": NCMECSignalMetadata({101: {"A2"}}),
    }
    ## No more data
    assert next(it, None) is None

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
