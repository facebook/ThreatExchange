# Copyright (c) Meta Platforms, Inc. and affiliates.

import pytest

from threatexchange.exchanges.clients.techagainstterrorism.tests.test_api import api
from threatexchange.exchanges.impl.techagainstterrorism_api import (
    TATSignalExchangeAPI,
)
from threatexchange.exchanges.fetch_state import FetchedSignalMetadata
from threatexchange.exchanges.clients.techagainstterrorism.api import TATHashListAPI


@pytest.fixture
def exchange(api: TATHashListAPI, monkeypatch: pytest.MonkeyPatch):
    signal_exchange = TATSignalExchangeAPI("user", "pass")
    monkeypatch.setattr(signal_exchange, "get_client", lambda: api)
    return signal_exchange


def test_fetch(exchange: TATSignalExchangeAPI):
    it = exchange.fetch_iter([], None)
    delta = next(it)

    updates = delta.updates

    assert len(updates) == 3

    expected_updates = {
        ("video_md5", "123abc"): FetchedSignalMetadata(),
        ("video_md5", "456def"): FetchedSignalMetadata(),
        ("pdq", "789ghi"): FetchedSignalMetadata(),
    }

    for key in expected_updates:
        assert key in updates
        assert isinstance(updates[key], FetchedSignalMetadata)

    assert set(delta.updates) == set(expected_updates)
