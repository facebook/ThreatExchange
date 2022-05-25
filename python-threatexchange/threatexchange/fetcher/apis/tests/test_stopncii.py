# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import pytest
import typing as t

from threatexchange.fetcher.fetch_state import AggregateSignalOpinionCategory
from threatexchange.fetcher.simple.state import SimpleFetchDelta

from threatexchange.stopncii.tests.test_api import api
from threatexchange.fetcher.apis.stop_ncii_api import (
    StopNCIICheckpoint,
    StopNCIISignalExchangeAPI,
    StopNCIISignalMetadata,
)
from threatexchange.fetcher.collab_config import CollaborationConfigWithDefaults
from threatexchange.fetcher.fetch_api import SignalExchangeAPI

from threatexchange.stopncii.api import StopNCIIAPI


@pytest.fixture
def fetcher(api: StopNCIIAPI):
    signal_exchange = StopNCIISignalExchangeAPI(None, None)
    signal_exchange._api = api
    return signal_exchange


def test_fetch(fetcher: SignalExchangeAPI, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("time.time", lambda: 10**8)
    collab = CollaborationConfigWithDefaults("Test")
    delta = t.cast(SimpleFetchDelta, fetcher.fetch_once([], collab, None))

    assert delta.has_more() is True
    assert delta.record_count() == 2

    checkpoint: StopNCIICheckpoint = delta.next_checkpoint()
    assert checkpoint.get_progress_timestamp() == 1625175071
    assert checkpoint.is_stale() is False
    assert checkpoint.update_time == 1625175071
    assert checkpoint.last_fetch_time == 10**8

    updates = delta.update_record
    assert len(updates) == 2
    assert {t[0] for t in updates} == {"pdq"}

    tt = tuple(updates.values())
    a = t.cast(StopNCIISignalMetadata, tt[0])
    b = t.cast(StopNCIISignalMetadata, tt[1])
    assert len(a.feedbacks) == 0
    ao = a.get_as_aggregate_opinion()
    assert ao.category == AggregateSignalOpinionCategory.WORTH_INVESTIGATING
    assert ao.tags == set()

    assert len(b.feedbacks) == 0
    bo = b.get_as_aggregate_opinion()
    assert bo.category == AggregateSignalOpinionCategory.WORTH_INVESTIGATING
    assert bo.tags == set()

    delta = t.cast(SimpleFetchDelta, fetcher.fetch_once([], collab, None))
    assert delta.has_more() is False
    assert delta.record_count() == 1
    updates = delta.update_record
    assert len(updates) == 1
    assert "pdq" == tuple(updates)[0][0]
    a = t.cast(StopNCIISignalMetadata, tuple(updates.values())[0])
    ao = a.get_as_aggregate_opinion()
    assert ao.category == AggregateSignalOpinionCategory.TRUE_POSITIVE
    assert ao.tags == {"Nude", "Objectionable"}
