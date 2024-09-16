# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t
import pytest

from threatexchange.exchanges.clients.techagainstterrorism.tests.test_api import api
from threatexchange.exchanges.impl.techagainstterrorism_api import (
    TATSignalExchangeAPI,
)

from threatexchange.exchanges.clients.techagainstterrorism.api import (
    TATHashListAPI
)


@pytest.fixture
def exchange(api: TATHashListAPI, monkeypatch: pytest.MonkeyPatch):
    signal_exchange = TATSignalExchangeAPI("user", "pass")
    monkeypatch.setattr(signal_exchange, "get_client", lambda: api)
    return signal_exchange

def test_fetch(exchange: TATSignalExchangeAPI, monkeypatch: pytest.MonkeyPatch):
    it = exchange.fetch_iter([], None)
    delta = next(it)
    assert delta.checkpoint.is_stale() is True

    





    
