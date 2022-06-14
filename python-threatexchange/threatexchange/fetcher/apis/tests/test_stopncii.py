# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import pytest
import typing as t

from threatexchange.fetcher.fetch_state import AggregateSignalOpinionCategory
from threatexchange.stopncii.tests.test_api import api

from threatexchange.fetcher.apis.stop_ncii_api import (
    StopNCIISignalExchangeAPI,
)
from threatexchange.fetcher.collab_config import CollaborationConfigWithDefaults

from threatexchange.stopncii.api import StopNCIIAPI


@pytest.fixture
def fetcher(api: StopNCIIAPI):
    signal_exchange = StopNCIISignalExchangeAPI(None, None)
    signal_exchange._api = api
    return signal_exchange


def test_fetch(fetcher: StopNCIISignalExchangeAPI, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("time.time", lambda: 10**8)
    collab = CollaborationConfigWithDefaults("Test")
    it = fetcher.fetch_iter([], collab, None)
    delta = next(it)

    assert len(delta.updates) == 2

    assert delta.checkpoint.get_progress_timestamp() == 1625175071
    assert delta.checkpoint.is_stale() is False
    assert delta.checkpoint.update_time == 1625175071
    assert delta.checkpoint.last_fetch_time == 10**8

    updates = delta.updates
    assert {t[0] for t in updates} == {"pdq"}

    tt = tuple(updates.values())
    a = tt[0]
    b = tt[1]
    assert a is not None
    assert b is not None
    assert len(a.feedbacks) == 0
    ao = a.get_as_aggregate_opinion()
    assert ao.category == AggregateSignalOpinionCategory.WORTH_INVESTIGATING
    assert ao.tags == set()

    assert len(b.feedbacks) == 0
    bo = b.get_as_aggregate_opinion()
    assert bo.category == AggregateSignalOpinionCategory.WORTH_INVESTIGATING
    assert bo.tags == set()

    # Second fetch
    delta = next(it)
    assert len(delta.updates) == 1
    assert "pdq" == tuple(delta.updates)[0][0]
    a = tuple(delta.updates.values())[0]
    assert a is not None
    ao = a.get_as_aggregate_opinion()
    assert ao.category == AggregateSignalOpinionCategory.TRUE_POSITIVE
    assert ao.tags == {"Nude", "Objectionable"}

    assert next(it, None) is None  # We fetched everything
