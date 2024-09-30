# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Simple implementation for the NCMEC hash sharing XML API

You can find the complete documentation at 
https://report.cybertip.org/hashsharing/v2/documentation.pdf
"""

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum, unique
import logging
import time
import typing as t
from io import BytesIO
import html
import urllib.parse

import requests
from urllib3.util.retry import Retry
from threatexchange.exchanges.clients.utils.common import TimeoutHTTPAdapter


_DATE_FORMAT_STR = "%Y-%m-%dT%H:%M:%SZ"
_DEFAULT_ELE = ET.Element("")

T = t.TypeVar("T")


def nullthrows(v: t.Optional[T]) -> T:
    """Typing helper"""
    assert v is not None
    return v


class _XMLWrapper:
    """
    Simpler wrapper around XML element for typing and null checking.

    To use the raw methods, just use .element
    """

    def __init__(self, e: ET.Element) -> None:
        self.element = e

    def __getitem__(self, key: str) -> "_XMLWrapper":
        """Asserts child with name exists"""
        child = self.element.findall(key)
        if not child:
            raise IndexError
        if len(child) != 1:
            raise ValueError(f"More than one child named {key}")
        return _XMLWrapper(child[0])

    def maybe(self, key: str, *rest: str) -> "_XMLWrapper":
        """Gets a child node or a placeholder for chaining"""
        curr = self.element
        for k in (key,) + rest:
            child = curr.find(k)
            if child is None:
                return _XMLWrapper(_DEFAULT_ELE)
            curr = child
        return _XMLWrapper(curr)

    @property
    def text(self) -> str:
        """Assert non-null text"""
        return nullthrows(self.element.text)

    @property
    def has_text(self) -> bool:
        """
        Returns true if tag is of the form <a>foo</a>
        Implies that .text will not throw.

        Returns false for <a/>
        Still returns true for <a></a>
        """
        return self.element.text is not None

    @property
    def tag(self) -> str:
        """Suger for getting the tag name"""
        return self.element.tag

    def __len__(self) -> int:
        return len(self.element)

    def __bool__(self) -> bool:
        """True if not a non-existant element from .maybe()"""
        return self.element is not _DEFAULT_ELE

    def __iter__(self) -> t.Iterator["_XMLWrapper"]:
        """Iterate over children"""
        for child in self.element:
            yield _XMLWrapper(child)

    def __str__(self) -> str:
        return f"<{self.tag}>{self.element.text or '...'}</{self.tag}>"

    # Because these methods are named after types it messes
    # with typechecking
    def int(self, key: str) -> int:
        """Assert property exists and return as int"""
        return int(nullthrows(self.element.get(key)))

    def str(self, key: str) -> str:
        """Assert property exists and return as str"""
        return nullthrows(self.element.get(key))


@dataclass
class StatusResult:
    esp_id: int
    esp_name: str


@unique
class NCMECEntryType(Enum):
    image = "image"
    video = "video"


@unique
class NCMECFeedbackType(Enum):
    md5 = "MD5"
    sha1 = "SHA1"
    pdna = "PDNA"
    pdq = "PDQ"
    netclean = "NETCLEAN"
    videntifier = "VIDENTIFIER"
    tmk_pdqf = "TMK_PDQF"
    ssvh_pdna = "SSVH_PDNA"
    ssvh_safer_hash = "SSVH_SAFER_HASH"


@dataclass
class NCMECEntryUpdate:
    id: str
    member_id: int
    entry_type: NCMECEntryType
    deleted: bool
    classification: t.Optional[str]
    fingerprints: t.Dict[str, str]
    feedback: t.List[t.Dict[str, t.Any]]

    @classmethod
    def from_xml(cls, xml: _XMLWrapper) -> "NCMECEntryUpdate":
        type_str = xml.tag.lower()
        deleted = type_str.startswith("deleted")
        if deleted:
            type_str = type_str[len("deleted") :]

        return cls(
            id=xml["id"].text,
            member_id=xml["member"].int("id"),
            entry_type=NCMECEntryType(type_str),
            deleted=deleted,
            classification=xml.maybe("classification").element.text,
            fingerprints={
                x.tag: x.text for x in xml.maybe("fingerprints") if x.has_text
            },
            feedback=(
                [
                    {
                        "sentiment": x.tag,  # "affirmativeFeedback" or "negativeFeedback"
                        "type": x.str("type"),
                        "latest_feedback_time": x.str("lastUpdateTimestamp"),
                        "members": [
                            {"id": m.str("id"), "name": m.text}
                            for m in x.maybe("members")
                            if m.has_text
                        ],
                        "reasons": [
                            {
                                "guid": r.maybe("reason").str("guid"),
                                "name": r.maybe("reason").str("name"),
                                "type": r.maybe("reason").str("type"),
                                "members": [
                                    {"id": m.str("id"), "name": m.text}
                                    for m in x.maybe("members")
                                ],
                            }
                            for r in x.maybe("reasons")
                            if r.maybe("reason")
                        ],
                    }
                    for x in xml.maybe("feedback")
                ]
                if xml.maybe("feedback").has_text
                else []
            ),
        )


class GetEntriesNextInfo(t.NamedTuple):
    """Wrapper around parsed "next" param data. Fields match param names"""

    start: int  # Might be- the start ID of the next fetch
    size: int  # How many records to fetch (always seems to be 1000)
    max: int  # The largest id in the time range

    @classmethod
    def from_next(cls, next_: str) -> t.Optional["GetEntriesNextInfo"]:
        s = html.unescape(next_)
        parsed = urllib.parse.parse_qs(s)
        start = parsed.get("start")
        size = parsed.get("size")
        max_ = parsed.get("max")
        if not start or not size or not max_:
            return None
        return GetEntriesNextInfo(int(start[0]), int(size[0]), int(max_[0]))


@dataclass
class GetEntriesResponse:
    updates: t.List[NCMECEntryUpdate]
    max_timestamp: int
    next: str

    @classmethod
    def from_xml(cls, xml: _XMLWrapper, fallback_max_time: int) -> "GetEntriesResponse":
        updates: t.List[NCMECEntryUpdate] = []
        max_ts = 0

        for content_xml in (xml.maybe("images"), xml.maybe("videos")):
            if not content_xml or not len(content_xml):
                continue
            max_ts = max(
                max_ts,
                int(
                    datetime.strptime(content_xml.str("maxTimestamp"), _DATE_FORMAT_STR)
                    .replace(tzinfo=timezone.utc)
                    .timestamp()
                ),
            )
            updates.extend(NCMECEntryUpdate.from_xml(c) for c in content_xml)

        next_ = xml.maybe("paging", "next").element.text or ""
        return cls(updates, max_ts or fallback_max_time, next_)

    def get_next_info(self) -> t.Optional[GetEntriesNextInfo]:
        if not self.next:
            return None
        return GetEntriesNextInfo.from_next(self.next)

    @property
    def estimated_entries_in_range(self) -> int:
        """Uses the "next" params to try and guess entries in range"""
        if not self.next:
            return len(self.updates)
        info = self.get_next_info()
        return (
            len(self.updates) + 1  # Parse error of some kind
            if info is None
            else info.max - info.start + len(self.updates)
        )


# TODO: once we know the shape of response, finish this class
@dataclass
class UpdateEntryResponse:
    updates: t.List[NCMECEntryUpdate]

    @classmethod
    def from_xml(
        cls, xml: _XMLWrapper, fallback_max_time: int
    ) -> "UpdateEntryResponse":
        updates: t.List[NCMECEntryUpdate] = []

        for content_xml in (xml.maybe("images"), xml.maybe("videos")):
            if not content_xml or not len(content_xml):
                continue
            updates.extend(NCMECEntryUpdate.from_xml(c) for c in content_xml)

        return cls(updates)


@dataclass
class GetFeedbackReasonsResponse:
    reasons: t.List[t.Dict[str, str]]

    @classmethod
    def from_xml(cls, xml: _XMLWrapper) -> "GetFeedbackReasonsResponse":
        reasons = []
        for reason in xml.maybe("availableFeedbackReasons"):
            reasons.append(
                {
                    "guid": reason.str("guid"),
                    "name": reason.str("name"),
                    "type": reason.str("type"),
                }
            )
        return cls(reasons)


@unique
class NCMECEndpoint(Enum):
    status = "status"
    entries = "entries"
    members = "members"
    feedback = "feedback"


class NCMECEnvironment(Enum):
    """
    Which 'Environment' to connect to.

    Environments differ by who is allowed to read or write, as well as what
    content exists on them.
    """

    Industry = "https://report.cybertip.org/hashsharing"
    NGO = "https://hashsharing.ncmec.org/npo"
    Exploitative = "https://hashsharing.ncmec.org/exploitative"

    test_Industry = "https://exttest.cybertip.org/hashsharing"
    test_NGO = "https://hashsharing-test.ncmec.org/npo"
    test_Exploitative = "https://hashsharing-test.ncmec.org/exploitative"


class NCMECHashAPI:
    """
    A wrapper around the NCMEC hash exchange API.

    Not to be confused with the cybertips API, which is for submitting illegal
    content, the hash exchange API is for submitting signals (or 'fingerprints'
    in the NCMEC parlance).

    Depending on which API you are connecting to, what is inside the database
    may differ greatly in exact topic. See NCMECEnvironment as well as NCMEC's
    documentation.
    """

    VERSION: t.ClassVar[str] = "v2"

    ENTRIES_PER_FETCH: t.ClassVar[int] = 1000

    def __init__(
        self,
        username: str,
        password: str,
        environment: NCMECEnvironment,
        member_id: t.Optional[str] = None,
        reasons_map: t.Dict[str, t.List[t.Dict[str, str]]] = {},
    ) -> None:
        assert is_valid_user_pass(username, password)
        self.username = username
        self.password = password
        self._base_url = environment.value
        self.member_id = member_id
        self.reasons_map = reasons_map or {}

    def _get_session(self) -> requests.Session:
        """
        Custom requests session

        Ideally, should be used within a context manager:
        ```
        with self._get_session() as session:
            session.get()...
        ```
        """

        session = requests.Session()
        session.auth = (self.username, self.password)
        session.mount(
            self._base_url,
            adapter=TimeoutHTTPAdapter(
                timeout=60,
                max_retries=Retry(
                    total=4,
                    status_forcelist=[429, 500, 502, 503, 504],
                    # No retry for post. Could probably add timeout...
                    allowed_methods=["HEAD", "GET", "OPTIONS"],
                    backoff_factor=0.2,  # ~1.5 seconds of retries
                ),
            ),
        )
        return session

    def _get(
        self, endpoint: NCMECEndpoint, *, path: str = "", next_: str = "", **params
    ) -> ET.Element:
        """
        Perform an HTTP GET request, and return the XML response payload.

        Same timeouts and retry strategy as `_get_session` above.
        """

        url = "/".join((self._base_url, self.VERSION, endpoint.value))
        if path:
            url = "/".join((url, path))
        if next_:
            url = self._base_url + next_
            params = {}

        with self._get_session() as session:
            response = session.get(url, params=params)
        # Gate this log just in case decode() blows up
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.debug("GET %s returned: %s", endpoint, response.content.decode())
        response.raise_for_status()
        # Namespaces don't really add anything here, so let's remove them
        it = ET.iterparse(BytesIO(response.content))
        for _, el in it:
            _ns, has_namespace, postfix = el.tag.partition("}")
            if has_namespace:
                el.tag = postfix
        return it.root  # type: ignore

    def _post(self, endpoint: NCMECEndpoint, *, data=None) -> t.Any:
        """
        Perform an HTTP POST request, and return the XML response payload.

        No timeout or retry strategy.
        """

        url = "/".join((self._base_url, self.VERSION, endpoint.value))
        with self._get_session() as session:
            response = session.post(url, data=data)
            response.raise_for_status()
            return response

    def _put(
        self,
        endpoint: NCMECEndpoint,
        *,
        member_id: t.Optional[str] = None,
        entry_id: t.Optional[str] = None,
        feedback_type: t.Optional[NCMECFeedbackType] = None,
        data=None,
    ) -> t.Any:
        """
        Perform an HTTP PUT request, and return the XML response payload.

        No timeout or retry strategy.
        """

        url = "/".join((self._base_url, self.VERSION, endpoint.value))
        if feedback_type and member_id and entry_id:
            url = "/".join(
                (
                    self._base_url,
                    endpoint.value,
                    member_id,
                    entry_id,
                    feedback_type.value,
                    NCMECEndpoint.feedback.value,
                )
            )
        with self._get_session() as session:
            response = session.put(url, data=data)
            response.raise_for_status()
            return response

    def status(self) -> StatusResult:
        """Query the status endpoint, which tells you who you are."""
        response = self._get(NCMECEndpoint.status)
        member = _XMLWrapper(response)["member"]
        self.member_id = member.str("id")
        return StatusResult(member.int("id"), member.text)

    def members(self) -> t.List[StatusResult]:
        """Query the members endpoint, which gives you a list of esps"""
        response = self._get(NCMECEndpoint.members)
        return [
            StatusResult(member.int("id"), member.text)
            for member in _XMLWrapper(response)
        ]

    def feedback_reasons(self) -> GetFeedbackReasonsResponse:
        """Get the possible negative feedback reasons for each feedback type"""
        for feedbackType in NCMECFeedbackType:
            resp = self._get(
                NCMECEndpoint.feedback, path=f"{feedbackType.value}/reasons"
            )
            reasonsResp = GetFeedbackReasonsResponse.from_xml(_XMLWrapper(resp))
            self.reasons_map[feedbackType.value] = reasonsResp.reasons

        return reasonsResp

    def get_entries(
        self,
        *,
        start_timestamp: int = 0,
        end_timestamp: int = 0,
        next_: str = "",
    ) -> GetEntriesResponse:
        """
        Fetch a series of update records from the hash API.

        DANGER! The NCMEC API does not return entries in time order! If you
        don't exhaust the entire iterator, you can't trust the max timestamp!
        """
        end_timestamp = end_timestamp or int(time.time())
        # Need a dict here for python keyword 'from'
        params: t.Dict[str, t.Any] = {
            "from": _date_format(start_timestamp),
        }
        response = self._get(
            NCMECEndpoint.entries,
            next_=next_,
            to=_date_format(end_timestamp),
            **params,
        )
        try:
            return GetEntriesResponse.from_xml(_XMLWrapper(response), int(time.time()))
        except Exception:
            raise Exception(
                "Failed to parse response: %s",
                ET.tostring(response, encoding="utf8", method="xml"),
            )

    def get_entries_iter(
        self, *, start_timestamp: int = 0, end_timestamp: int = 0
    ) -> t.Iterator[GetEntriesResponse]:
        """
        A simple wrapper around get_entries to keep fetching until complete.

        If you don't exhaust the iterator, you can't make any assumptions about how
        much of the data you have fetched. @see get_entries
        """
        has_more = True
        next_ = ""
        while has_more:
            result = self.get_entries(
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                next_=next_,
            )
            next_ = result.next
            has_more = bool(next_)
            yield result

    def submit_feedback(
        self,
        entry_id: str,
        feedback_type: NCMECFeedbackType,
        affirmative: bool,
        reason_id: t.Optional[str] = None,
    ) -> GetEntriesResponse:
        if not affirmative and not reason_id:
            raise ValueError("Negative feedback must have a reason_id")

        # need member_id to submit feedback
        if not self.member_id:
            self.status()

        # need valid reasons to submit negative feedback
        if not affirmative and not self.reasons_map:
            self.feedback_reasons()

        # Prepare the XML payload
        root = ET.Element("feedbackSubmission")
        root.set("xmlns", "https://hashsharing.ncmec.org/hashsharing/v2")
        vote = ET.SubElement(root, "affirmative" if affirmative else "negative")

        if not affirmative:
            valid_reason_ids = [
                reason["guid"] for reason in self.reasons_map[feedback_type.value]
            ]
            if reason_id not in valid_reason_ids:
                print(
                    "must choose from the following reasons: ",
                    self.reasons_map[feedback_type.value],
                )
                raise ValueError("Invalid reason_id")
            reasons = ET.SubElement(vote, "reasonIds")
            guid = ET.SubElement(reasons, "guid")
            guid.text = reason_id
        # ET.dump(root)

        resp = self._put(
            NCMECEndpoint.entries,
            member_id=self.member_id,
            entry_id=entry_id,
            feedback_type=feedback_type,
            data=ET.tostring(root),
        )

        # TODO: parse response here once we know the shape using UpdateEntryResponse
        return resp


def _date_format(timestamp: int) -> str:
    """ISO 8601 format yyyy-MM-dd'T'HH:mm:ss.SSSZ"""
    return datetime.fromtimestamp(timestamp).strftime(_DATE_FORMAT_STR)


def is_valid_user_pass(user: str, password: str) -> bool:
    return bool(user and password)  # Is there anything more we can do here?
