# Copyright (c) Meta Platforms, Inc. and affiliates.

import pytest
import typing as t

from threatexchange.exchanges.fetch_state import AggregateSignalOpinionCategory
from threatexchange.exchanges.clients.stopncii.tests.test_api import api

from threatexchange.exchanges.impl.stop_ncii_api import (
    StopNCIICredentials,
    StopNCIISignalExchangeAPI,
)
from threatexchange.exchanges.collab_config import CollaborationConfigWithDefaults

from threatexchange.exchanges.clients.stopncii.api import StopNCIIAPI, StopNCIIEndpoint


@pytest.fixture
def exchange(api: StopNCIIAPI):
    collab = CollaborationConfigWithDefaults("Test")
    return StopNCIISignalExchangeAPI(collab, api)


def test_fetch(exchange: StopNCIISignalExchangeAPI, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("time.time", lambda: 10**8)
    it = exchange.fetch_iter([], None)
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
    assert ao.category == AggregateSignalOpinionCategory.INVESTIGATION_SEED
    assert ao.tags == set()

    assert len(b.feedbacks) == 0
    bo = b.get_as_aggregate_opinion()
    assert bo.category == AggregateSignalOpinionCategory.INVESTIGATION_SEED
    assert bo.tags == set()

    # Second fetch
    delta = next(it)
    assert len(delta.updates) == 1
    assert "pdq" == tuple(delta.updates)[0][0]
    a = tuple(delta.updates.values())[0]
    assert a is not None
    ao = a.get_as_aggregate_opinion()
    assert ao.category == AggregateSignalOpinionCategory.POSITIVE_CLASS
    assert ao.tags == {"Nude", "Objectionable"}

    assert next(it, None) is None  # We fetched everything


@pytest.mark.parametrize(
    ("s", "base_url", "feedback_key"),
    [
        ("fetch,sub", None, None),
        ("fetch,sub,https://example.test", "https://example.test", None),
        ("fetch,sub,,feedback", None, "feedback"),
        ("fetch,sub,https://example.test,feedback", "https://example.test", "feedback"),
    ],
)
def test_credentials_from_str(
    s: str, base_url: t.Optional[str], feedback_key: t.Optional[str]
):
    creds = StopNCIICredentials._from_str(s)
    assert creds.fetch_function_key == "fetch"
    assert creds.subscription_key == "sub"
    assert creds.base_url_override == base_url
    assert creds.feedback_function_key == feedback_key


def test_credentials_from_str_invalid():
    with pytest.raises(ValueError):
        StopNCIICredentials._from_str("only_one_part")
    with pytest.raises(ValueError):
        StopNCIICredentials._from_str("a,b,c,d,e")


def test_for_collab_passes_feedback_key():
    collab = CollaborationConfigWithDefaults("Test")
    with_key = StopNCIISignalExchangeAPI.for_collab(
        collab, StopNCIICredentials._from_str("fetch,sub,,feedback")
    )
    assert with_key.api._function_keys[StopNCIIEndpoint.SubmitFeedback] == "feedback"
    without_key = StopNCIISignalExchangeAPI.for_collab(
        collab, StopNCIICredentials._from_str("fetch,sub")
    )
    assert StopNCIIEndpoint.SubmitFeedback not in without_key.api._function_keys
