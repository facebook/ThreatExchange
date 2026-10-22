# Copyright (c) Meta Platforms, Inc. and affiliates.

import pytest
import typing as t

from threatexchange.exchanges.fetch_state import AggregateSignalOpinionCategory
from threatexchange.exchanges.clients.stopncii.tests.test_api import (
    api,
    raise_malformed_json,
)

from threatexchange.exchanges.impl.stop_ncii_api import (
    MALFORMED_PAGE_MAX_CONSECUTIVE_SKIPS,
    MALFORMED_PAGE_SKIP_SEC,
    StopNCIICheckpoint,
    StopNCIISignalExchangeAPI,
    StopNCIISkippedWindow,
)
from threatexchange.exchanges.collab_config import CollaborationConfigWithDefaults

from threatexchange.exchanges.clients.stopncii.api import (
    StopNCIIAPI,
    StopNCIIEndpoint,
    StopNCIIMalformedResponseError,
)
from threatexchange.utils import dataclass_json


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


class FakeStopNCIIFeed:
    """
    One record every 5 minutes from start to now, served 15 minutes per page.

    Pages starting in [corrupt_start, corrupt_end) come back malformed.
    """

    PAGE_SEC = 15 * 60

    def __init__(self, start: int, now: int) -> None:
        self.now = now
        self.record_times = list(range(start + 1, now, 5 * 60))
        self.corrupt_start = 0
        self.corrupt_end = 0

    def expected_keys(self) -> t.Set[t.Tuple[str, str]]:
        return {("pdq", f"{ts:064x}") for ts in self.record_times}

    def get(self, endpoint: StopNCIIEndpoint, **params):
        assert endpoint == StopNCIIEndpoint.FetchHashes
        # Page tokens encode where the next page starts
        start = int(params.get("nextPageToken") or params["startTimestamp"])
        if self.corrupt_start <= start < self.corrupt_end:
            raise_malformed_json()
        records = [
            ts for ts in self.record_times if start <= ts < start + self.PAGE_SEC
        ]
        next_start = (
            records[-1] + 1 if records else min(start + self.PAGE_SEC, self.now)
        )
        has_more = next_start < self.record_times[-1]
        return {
            "count": len(records),
            "nextSetTimestamp": next_start,
            "nextPageToken": str(next_start) if has_more else None,
            "hasMoreRecords": has_more,
            "hashRecords": [
                {
                    "lastModtimestamp": ts,
                    "hashValue": f"{ts:064x}",
                    "hashStatus": "Active",
                    "caseNumbers": {},
                    "signalType": "ImagePDQ",
                }
                for ts in records
            ],
        }


NOW = 1_790_000_000
HOUR = 60 * 60


@pytest.fixture
def feed(monkeypatch: pytest.MonkeyPatch) -> FakeStopNCIIFeed:
    monkeypatch.setattr("time.time", lambda: NOW)
    return FakeStopNCIIFeed(NOW - 6 * HOUR, NOW)


def fetch_all(
    feed: FakeStopNCIIFeed,
    monkeypatch: pytest.MonkeyPatch,
    checkpoint: t.Optional[StopNCIICheckpoint],
) -> t.Tuple[t.Set[t.Tuple[str, str]], StopNCIICheckpoint]:
    client = StopNCIIAPI("", "")
    monkeypatch.setattr(client, "_get", feed.get)
    exchange = StopNCIISignalExchangeAPI(
        CollaborationConfigWithDefaults("Test"), client
    )
    keys: t.Set[t.Tuple[str, str]] = set()
    for delta in exchange.fetch_iter([], checkpoint):
        keys.update(delta.updates)
        checkpoint = delta.checkpoint
    assert checkpoint is not None
    # Checkpoints are stored as JSON, make sure the windows survive that
    return keys, dataclass_json.dataclass_loads(
        dataclass_json.dataclass_dumps(checkpoint), StopNCIICheckpoint
    )


def test_fetch_skips_malformed_window_then_fetches_it_once_fixed(
    feed: FakeStopNCIIFeed, monkeypatch: pytest.MonkeyPatch
):
    start = NOW - 6 * HOUR
    feed.corrupt_start = start + HOUR
    feed.corrupt_end = start + HOUR + 30 * 60

    keys, checkpoint = fetch_all(feed, monkeypatch, StopNCIICheckpoint(start, NOW - 60))
    # Fetching carried on past the malformed pages, up to now...
    assert checkpoint.update_time >= feed.record_times[-1]
    # ...but some records are missing, and the window they are in is recorded
    missing = feed.expected_keys() - keys
    assert missing
    assert len(checkpoint.skipped_windows) == 1
    window = checkpoint.skipped_windows[0]
    assert all(window.start <= int(h, 16) < window.end for _, h in missing)

    # StopNCII keeps serving malformed pages: still recorded, nothing lost
    keys_2, checkpoint = fetch_all(feed, monkeypatch, checkpoint)
    assert keys_2 == set()
    assert checkpoint.skipped_windows == [window]

    # StopNCII fixes their data: the next fetch picks up what was missing
    feed.corrupt_end = 0
    keys_3, checkpoint = fetch_all(feed, monkeypatch, checkpoint)
    assert missing <= keys_3
    assert checkpoint.skipped_windows == []
    assert keys | keys_3 == feed.expected_keys()


def test_fetch_raises_after_too_many_consecutive_skips(
    feed: FakeStopNCIIFeed, monkeypatch: pytest.MonkeyPatch
):
    start = NOW - 6 * HOUR
    feed.corrupt_start = 0
    feed.corrupt_end = NOW  # Everything is broken

    client = StopNCIIAPI("", "")
    monkeypatch.setattr(client, "_get", feed.get)
    exchange = StopNCIISignalExchangeAPI(
        CollaborationConfigWithDefaults("Test"), client
    )
    deltas = []
    with pytest.raises(StopNCIIMalformedResponseError):
        for delta in exchange.fetch_iter([], StopNCIICheckpoint(start, NOW - 60)):
            deltas.append(delta)

    assert len(deltas) == MALFORMED_PAGE_MAX_CONSECUTIVE_SKIPS
    assert all(not d.updates for d in deltas)
    # Consecutive skips are merged into one window, ending where we stopped
    last = deltas[-1].checkpoint
    skipped_to = start + MALFORMED_PAGE_SKIP_SEC * MALFORMED_PAGE_MAX_CONSECUTIVE_SKIPS
    assert last.update_time == skipped_to
    assert last.skipped_windows == [StopNCIISkippedWindow(start, skipped_to)]


def test_fetch_never_skips_past_now(
    feed: FakeStopNCIIFeed, monkeypatch: pytest.MonkeyPatch
):
    start = NOW - 2 * 60
    feed.corrupt_start = start
    feed.corrupt_end = NOW

    keys, checkpoint = fetch_all(feed, monkeypatch, StopNCIICheckpoint(start, NOW - 60))
    assert keys == set()
    assert checkpoint.update_time == NOW
    assert checkpoint.skipped_windows == [StopNCIISkippedWindow(start, NOW)]


def test_checkpoint_without_skipped_windows_still_loads():
    # As stored before skipped_windows existed
    checkpoint = dataclass_json.dataclass_load_dict(
        {"update_time": 1625175071, "last_fetch_time": 10**8}, StopNCIICheckpoint
    )
    assert checkpoint == StopNCIICheckpoint(1625175071, 10**8, [])
