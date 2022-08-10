from unittest.mock import Mock
import pytest
import requests
from threatexchange.exchanges.clients.ncmec.hash_api import (
    NCMECEntryType,
    NCMECEntryUpdate,
    NCMECHashAPI,
    NCMECEnvironment,
)

STATUS_XML = """
<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<status xmlns="https://hashsharing.ncmec.org/hashsharing/v2">
    <ipAddress>127.0.0.1</ipAddress>
    <username>testington</username>
    <member id="1">Sir Testington</member>
</status>
""".strip()

NEXT_UNESCAPED = (
    "/v2/entries?from=2017-10-20T00%3A00%3A00.000Z"
    "&to=2017-10-30T00%3A00%3A00.000Z&start=2001&size=1000&max=3000"
)

NEXT_UNESCAPED2 = (
    "/v2/entries?from=2017-10-20T00%3A00%3A00.000Z"
    "&to=2017-10-30T00%3A00%3A00.000Z&start=3001&size=1000&max=4000"
)
NEXT_UNESCAPED3 = (
    "/v2/entries?from=2017-10-20T00%3A00%3A00.000Z"
    "&to=2017-10-30T00%3A00%3A00.000Z&start=4001&size=1000&max=5000"
)

ENTRIES_XML = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<queryResult xmlns="https://hashsharing.ncmec.org/hashsharing/v2">
    <images count="2" maxTimestamp="2017-10-24T15:10:00Z">
        <image>
            <member id="42">Example Member</member>
            <timestamp>2017-10-24T15:00:00Z</timestamp>
            <id>image1</id>
            <classification>A1</classification>
            <fingerprints>
                <md5>a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1</md5>
                <sha1>a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1</sha1>
                <pdna>a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1...</pdna>
            </fingerprints>
        </image>
        <deletedImage>
            <member id="43">Example Member2</member>
            <id>image4</id>
            <timestamp>2017-10-24T15:10:00Z</timestamp>
        </deletedImage>
    </images>
    <videos count="2" maxTimestamp="2017-10-24T15:20:00Z">
        <video>
            <member id="42">Example Member</member>
            <timestamp>2017-10-24T15:00:00Z</timestamp>
            <id>video1</id>
            <fingerprints>
                <md5>b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1</md5>
                <sha1>b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1b1</sha1>
            </fingerprints>
        </video>
        <deletedVideo>
            <member id="42">Example Member</member>
            <id>video4</id>
            <timestamp>2017-10-24T15:20:00Z</timestamp>
        </deletedVideo>
    </videos>
    <paging>
        <next>/v2/entries?from=2017-10-20T00%3A00%3A00.000Z&amp;to=2017-10-30T00%3A00%3A00.000Z&amp;start=2001&amp;size=1000&amp;max=3000</next>
    </paging>
</queryResult>
""".strip()


ENTRIES_XML2 = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<queryResult xmlns="https://hashsharing.ncmec.org/hashsharing/v2">
    <images count="1" maxTimestamp="2019-10-24T15:10:00Z">
        <image>
            <member id="42">Example Member</member>
            <timestamp>2019-10-24T15:00:00Z</timestamp>
            <id>image10</id>
            <classification>A1</classification>
            <fingerprints>
                <md5>b1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1</md5>
                <sha1>b1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1</sha1>
                <pdna>b1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1...</pdna>
            </fingerprints>
        </image>
    </images>
    <paging>
        <next>/v2/entries?from=2017-10-20T00%3A00%3A00.000Z&amp;to=2017-10-30T00%3A00%3A00.000Z&amp;start=3001&amp;size=1000&amp;max=4000</next>
    </paging>
</queryResult>
""".strip()

# This example isn't in the documentation, but shows how updates work
ENTRIES_XML3 = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<queryResult xmlns="https://hashsharing.ncmec.org/hashsharing/v2">
    <videos count="2" maxTimestamp="2019-11-25T15:10:00Z">
        <video>
            <member id="101">TX Example</member>
            <timestamp>2019-11-25T15:10:00Z</timestamp>
            <id>willupdate</id>
            <classification>A1</classification>
            <fingerprints>
                <md5>facefacefacefacefacefacefaceface</md5>
            </fingerprints>
        </video>
        <video>
            <member id="101">TX Example</member>
            <timestamp>2019-11-24T15:10:00Z</timestamp>
            <id>willdelete</id>
            <classification>A1</classification>
            <fingerprints>
                <md5>bacebacebacebacebacebacebacebace</md5>
            </fingerprints>
        </video>
    </videos>
    <paging>
        <next>/v2/entries?from=2017-10-20T00%3A00%3A00.000Z&amp;to=2017-10-30T00%3A00%3A00.000Z&amp;start=4001&amp;size=1000&amp;max=5000</next>
    </paging>
</queryResult>
""".strip()

ENTRIES_XML4 = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<queryResult xmlns="https://hashsharing.ncmec.org/hashsharing/v2">
    <videos count="2" maxTimestamp="2019-11-24T15:10:00Z">
        <video>
            <member id="101">TX Example</member>
            <timestamp>2019-11-24T15:10:00Z</timestamp>
            <id>willupdate</id>
            <classification>A2</classification>
            <fingerprints>
                <md5>facefacefacefacefacefacefaceface</md5>
            </fingerprints>
        </video>
        <deletedVideo>
            <member id="101">TX Example</member>
            <timestamp>2019-11-25T15:10:00Z</timestamp>
            <id>willdelete</id>
        </deletedVideo>
    </videos>
</queryResult>
""".strip()


def mock_get_impl(url: str, **params):
    content = ENTRIES_XML
    if url.endswith(NEXT_UNESCAPED):
        content = ENTRIES_XML2
    if url.endswith(NEXT_UNESCAPED2):
        content = ENTRIES_XML3
    if url.endswith(NEXT_UNESCAPED3):
        content = ENTRIES_XML4
    # Void your warantee by messing with requests state
    resp = requests.Response()
    resp._content = content.encode()
    resp.status_code = 200
    resp.content  # Set the rest of Request's internal state
    return resp


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch):
    api = NCMECHashAPI("fake_user", "fake_pass", NCMECEnvironment.test_Industry)
    session = None
    session = Mock(
        strict_spec=["get", "__enter__", "__exit__"],
        get=mock_get_impl,
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
