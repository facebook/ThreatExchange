# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import pytest

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
    first_update = {
        "b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1": NCMECSignalMetadata({42: set()})
    }
    third_update = dict(first_update)
    third_update.update(
        {
            "facefacefacefacefacefacefaceface": NCMECSignalMetadata({101: {"A1"}}),
            "bacebacebacebacebacebacebacebace": NCMECSignalMetadata({101: {"A1"}}),
        }
    )
    forth_update = dict(first_update)
    forth_update.update(
        {
            "facefacefacefacefacefacefaceface": NCMECSignalMetadata({101: {"A2"}}),
        }
    )

    # Fetch 1
    delta = next(it)
    assert len(delta.updates) == 4
    total_updates = fetcher.naive_fetch_merge(None, delta.updates)

    assert delta.checkpoint.get_progress_timestamp() == 1508858400
    assert delta.checkpoint.is_stale() is False
    assert delta.checkpoint.max_timestamp == 1508858400

    assert set(delta.updates) == {"43-image4", "42-image1", "42-video1", "42-video4"}

    as_signals = NCMECSignalExchangeAPI.naive_convert_to_signal_type(
        [VideoMD5Signal], total_updates
    )[VideoMD5Signal]
    assert as_signals == first_update

    delta = next(it)
    assert len(delta.updates) == 1

    assert {t for t in delta.updates} == {"42-image10"}
    total_updates = fetcher.naive_fetch_merge(total_updates, delta.updates)
    as_signals = NCMECSignalExchangeAPI.naive_convert_to_signal_type(
        [VideoMD5Signal], total_updates
    )[VideoMD5Signal]
    assert as_signals == first_update

    ## Fetch 3
    delta = next(it)
    assert len(delta.updates) == 2
    assert {t for t in delta.updates} == {"101-willdelete", "101-willupdate"}
    total_updates = fetcher.naive_fetch_merge(total_updates, delta.updates)

    as_signals = NCMECSignalExchangeAPI.naive_convert_to_signal_type(
        [VideoMD5Signal], total_updates
    )[VideoMD5Signal]
    assert as_signals == third_update

    ## Fetch 4
    delta = next(it)
    assert len(delta.updates) == 2
    assert {t for t in delta.updates} == {"101-willdelete", "101-willupdate"}
    total_updates = fetcher.naive_fetch_merge(total_updates, delta.updates)

    as_signals = NCMECSignalExchangeAPI.naive_convert_to_signal_type(
        [VideoMD5Signal], total_updates
    )[VideoMD5Signal]
    assert as_signals == forth_update

    ## No more data
    assert next(it, None) is None
