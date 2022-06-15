# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import pytest
import typing as t

from threatexchange.fetcher.fetch_state import AggregateSignalOpinionCategory

from threatexchange.ncmec.tests.test_hash_api import api
from threatexchange.fetcher.apis.ncmec_api import (
    NCMECCollabConfig,
    NCMECSignalExchangeAPI,
    NCMECSignalMetadata,
    NCMECUpdate,
)

from threatexchange.ncmec.hash_api import NCMECEnvironment, NCMECHashAPI

from threatexchange.signal_type.md5 import VideoMD5Signal


@pytest.fixture
def fetcher(api: NCMECHashAPI):
    signal_exchange = NCMECSignalExchangeAPI("user", "pass")
    signal_exchange._api = api
    return signal_exchange


def test_fetch(fetcher: NCMECSignalExchangeAPI, monkeypatch: pytest.MonkeyPatch):
    collab = NCMECCollabConfig(NCMECEnvironment.Industry, "Test")
    it = fetcher.fetch_iter([], collab, None)
    delta = next(it)

    assert len(delta.updates) == 4

    assert delta.checkpoint.get_progress_timestamp() == 1508858400
    assert delta.checkpoint.is_stale() is False
    assert delta.checkpoint.max_timestamp == 1508858400

    assert set(delta.updates) == {"43-image4", "42-image1", "42-video1", "42-video4"}
    updates = delta.updates

    assert_expected_updates(updates)

    delta = next(it)
    assert len(delta.updates) == 1

    assert {t for t in delta.updates} == {"42-image10"}
    updates = fetcher.naive_fetch_merge(updates, delta.updates)
    assert_expected_updates(updates)


def assert_expected_updates(updates: NCMECUpdate):
    """We can do this because the return of the API return is hardcoded"""
    as_signal_types = NCMECSignalExchangeAPI.naive_convert_to_signal_type(
        [VideoMD5Signal], updates
    )

    assert len(as_signal_types) == 1
    vmd5s = as_signal_types[VideoMD5Signal]
    assert len(vmd5s) == 1
    signal_metadata: NCMECSignalMetadata
    vmd5, signal_metadata = next(iter(vmd5s.items()))
    assert vmd5 == "b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1"

    opinions = signal_metadata.get_as_opinions()
    assert len(opinions) == 1
    opinion = opinions[0]
    assert opinion.owner == 42
    agg = signal_metadata.get_as_aggregate_opinion()
    assert agg.category == AggregateSignalOpinionCategory.TRUE_POSITIVE
    assert agg.tags == set()
