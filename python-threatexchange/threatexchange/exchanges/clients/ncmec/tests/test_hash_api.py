# Copyright (c) Meta Platforms, Inc. and affiliates.

from unittest.mock import Mock
import typing as t
import pytest
import requests
from threatexchange.exchanges.clients.ncmec.hash_api import (
    NCMECEntryType,
    NCMECEntryUpdate,
    FingerprintType,
    NCMECHashAPI,
    NCMECEnvironment,
    FeedbackType,
)
from threatexchange.exchanges.clients.ncmec.tests.data import (
    ENTRIES_LARGE_FINGERPRINTS,
    ENTRIES_XML,
    ENTRIES_XML2,
    ENTRIES_XML3,
    ENTRIES_XML4,
    NEXT_UNESCAPED,
    NEXT_UNESCAPED2,
    NEXT_UNESCAPED3,
    STATUS_XML,
)


def mock_get_impl(url: str, **params):
    content = ENTRIES_XML
    if url.endswith(NEXT_UNESCAPED):
        content = ENTRIES_XML2
    elif url.endswith(NEXT_UNESCAPED2):
        content = ENTRIES_XML3
    elif url.endswith(NEXT_UNESCAPED3):
        content = ENTRIES_XML4
    elif url.endswith("/status"):
        content = STATUS_XML
    # Void your warantee by messing with requests state
    resp = requests.Response()
    resp._content = content.encode()
    resp.status_code = 200
    resp.content  # Set the rest of Request's internal state
    return resp


def set_api_return(content: str):
    # Some day support next
    # def next_str(i: int) -> str:
    #     return (
    #         "/v2/entries?from=2017-10-20T00%3A00%3A00.000Z"
    #         f"&to=2017-10-30T00%3A00%3A00.000Z&start={i * 1000 + 1}&size=1000&max={(i + 1) * 1000}"
    #     )
    #
    # content = xmls[(int(qs.get("start", "1")) - 1) // 1000]

    def _mock_get_impl(url: str, **params):
        resp = requests.Response()
        resp._content = content.encode()
        resp.status_code = 200
        resp.content  # Set the rest of Request's internal state
        return resp

    return _mock_get_impl


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch):
    api = NCMECHashAPI("fake_user", "fake_pass", NCMECEnvironment.test_Industry)
    session = None
    session = Mock(
        strict_spec=["get", "__enter__", "__exit__"],
        get=mock_get_impl,
        _put=Mock(),
        __enter__=lambda _: session,
        __exit__=lambda *args: None,
    )
    monkeypatch.setattr(api, "_get_session", lambda: session)
    return api


def assert_first_entry(entry: NCMECEntryUpdate) -> None:
    assert entry.id == "image1"
    assert entry.member_id == 42
    assert entry.entry_type == NCMECEntryType.image
    assert entry.deleted is False
    assert entry.fingerprints == {
        "md5": "a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1",
        "sha1": "a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1",
        "pdna": "a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1...",
    }


def assert_second_entry(entry: NCMECEntryUpdate) -> None:
    assert entry.id == "image4"
    assert entry.member_id == 43
    assert entry.entry_type == NCMECEntryType.image
    assert entry.deleted is True
    assert entry.fingerprints == {}


def assert_third_entry(entry: NCMECEntryUpdate) -> None:
    assert entry.id == "video1"
    assert entry.member_id == 42
    assert entry.entry_type == NCMECEntryType.video
    assert entry.deleted is False
    assert entry.fingerprints == {
        "md5": "b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1",
        "sha1": "b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1",
    }


def assert_fourth_entry(entry: NCMECEntryUpdate) -> None:
    assert entry.id == "video4"
    assert entry.member_id == 42
    assert entry.entry_type == NCMECEntryType.video
    assert entry.deleted is True
    assert entry.fingerprints == {}


def assert_fifth_entry(entry: NCMECEntryUpdate) -> None:
    assert entry.id == "image10"
    assert entry.member_id == 42
    assert entry.entry_type == NCMECEntryType.image
    assert entry.deleted is False
    assert entry.fingerprints == {
        "md5": "b1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1",
        "sha1": "b1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1",
        "pdna": "b1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1...",
    }


def test_mocked_status(api: NCMECHashAPI):
    assert api._my_esp is None
    result = api.status()
    assert result.esp_id == 1
    assert result.esp_name == "test member"
    assert result == api._my_esp


def test_mocked_get_hashes(api: NCMECHashAPI):
    result = api.get_entries()

    assert len(result.updates) == 4
    assert result.max_timestamp == 1508858400
    assert result.next != ""
    one, two, three, four = result.updates
    assert_first_entry(one)
    assert_second_entry(two)
    assert_third_entry(three)
    assert_fourth_entry(four)

    second_result = api.get_entries(next_=result.next)

    assert len(second_result.updates) == 1
    assert second_result.max_timestamp == 1571929800
    assert second_result.next != ""
    five = second_result.updates[0]
    assert_fifth_entry(five)

    # These later results don't need to be tested for this test, matters
    # for the SignalExchange API
    third_result = api.get_entries(next_=second_result.next)
    assert third_result.next != ""
    assert third_result not in (result, second_result)
    forth_result = api.get_entries(next_=third_result.next)
    assert forth_result not in (result, second_result, third_result)
    assert forth_result.next == ""

    # The other updates don't need to be tested here


def test_large_fingerprint_entries(monkeypatch):
    api = NCMECHashAPI("fake_user", "fake_pass", NCMECEnvironment.test_Industry)
    session = Mock(
        strict_spec=["get", "__enter__", "__exit__"],
        get=set_api_return(ENTRIES_LARGE_FINGERPRINTS),
        __enter__=lambda _: session,
        __exit__=lambda *args: None,
    )
    monkeypatch.setattr(api, "_get_session", lambda: session)

    result = api.get_entries()

    assert len(result.updates) == 1
    update = result.updates[0]
    assert len(update.fingerprints) == 1
    assert update.fingerprints == {"md5": "facefacefacefacefacefacefaceface"}
    assert result.next == ""


def test_feedback_entries(api: NCMECHashAPI):
    # We'll mock that we've already read our own ESP

    api.submit_feedback(1, "image1", FingerprintType.md5, FeedbackType.upvote)
    api.submit_feedback(
        1,
        "image1",
        FingerprintType.md5,
        FeedbackType.downvote,
        "01234567-abcd-0123-4567-012345678900",
    )
