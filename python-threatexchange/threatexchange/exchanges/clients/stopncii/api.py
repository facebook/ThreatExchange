# Copyright (c) Meta Platforms, Inc. and affiliates.

"""Simple implementation for the StopNCII REST API"""

from dataclasses import dataclass, field
import enum
import logging
import time
import typing as t

import dacite
import requests
from requests.exceptions import JSONDecodeError
from urllib3.util.retry import Retry
from threatexchange.exchanges.clients.utils.common import TimeoutHTTPAdapter

# How far to advance start_timestamp when a FetchHashes response body is
# malformed, so a single corrupt page cannot wedge fetching forever
# (the checkpoint can only advance on a successful page). Skipped windows
# can be re-fetched later once the server-side data is fixed.
MALFORMED_PAGE_SKIP_SECONDS: int = 600
# Bound how many corrupt windows one fetch_hashes_iter call will walk past,
# so a fetch from DEFAULT_START_TIME cannot spin on skip-requests until
# wall-clock "now".
MALFORMED_PAGE_MAX_SKIPS: int = 12


@enum.unique
class StopNCIISignalType(enum.Enum):
    """What the serialized hash represents"""

    Unknown = "Unknown"
    ImagePDQ = "ImagePDQ"
    VideoMD5 = "VideoMD5"
    VideoTMK = "VideoTMK"
    Text = "Text"
    URL = "URL"


@enum.unique
class StopNCIICaseStatus(enum.Enum):
    """The state of the user-submitted hash"""

    Unknown = "Unknown"
    Received = "Received"  # Initial state
    Active = "Active"  # Unclear what this represents
    Withdrawn = "Withdrawn"  # Should be deleted by client
    Deleted = "Deleted"  # Should be deleted by client


@enum.unique
class StopNCIICSPFeedbackValue(enum.Enum):
    """The feedback that a CSP has given on a hash"""

    Unknown = "Unknown"
    None_ = "None"  # Allows you to tag without associating a state
    QualityUnknown = "QualityUnknown"  # Unsure what this is used for
    PendingReview = "PendingReview"  # There was a match
    Blocked = "Blocked"  # Match reviewed, match was determined to be NCII
    NotBlocked = "NotBlocked"  # Match reviewed, inconclusive if NCII
    Withdrawn = "Withdrawn"  # Should be deleted by client
    Deleted = "Deleted"  # Should be deleted by client


@dataclass
class StopNCIICSPFeedback:
    """Feedback on a hash from a Content Service Provider"""

    feedbackValue: StopNCIICSPFeedbackValue  # What the feedback is
    tags: t.Set[str] = field(default_factory=set)  # Unstructured additional tags
    source: str = ""  # Name of the Content Service Provider (CSP)

    def as_dict_for_post(self) -> t.Dict[str, t.Any]:
        """The json-friendly format to send in post requests"""
        return {
            "tags": list(self.tags),
            "feedbackValue": self.feedbackValue.value,
        }


@dataclass
class StopNCIIHashRecord:
    """An aggregate record for a single hash from the StopNCII API"""

    lastModtimestamp: int  # Last update time
    signalType: StopNCIISignalType  # What the hashValue is
    hashValue: str  # The value of the hash
    hashStatus: StopNCIICaseStatus  # The "aggregate" case status
    caseNumbers: t.Dict[str, StopNCIICaseStatus]  # Individual cases that correspond
    # Feedback on hashes by CSPs
    CSPFeedbacks: t.List[StopNCIICSPFeedback] = field(default_factory=list)


@dataclass
class FetchHashesResponse:
    """
    Wrapper around the FetchHashes call response.

    Advantages of using a dataclass is the typing!
    """

    count: int  # How many records are there?
    nextPageToken: t.Optional[
        str
    ]  # Cursor for paginating, not valid over long periods of time
    nextSetTimestamp: int  # The best timestamp to use to store as a checkpoint
    hasMoreRecords: bool  # If the cursor is fully played out
    hashRecords: t.List[StopNCIIHashRecord]  # The records


@enum.unique
class StopNCIIEndpoint(enum.Enum):
    """Endpoints (with their own function keys) on StopNCII"""

    FetchHashes = "FetchHashes"
    SubmitHashes = "SubmitHashes"
    SubmitFeedback = "SubmitFeedback"


class StopNCIIAPI:
    """
    A wrapper around the StopNCII.org hash exchange API.

    Hashes are submitted by individual people to the portal at StopNCII.org,
    and Content Service Providers (CSPs), such as social networks, can provide
    feedback on the hashes on whether they are able to verify that the content
    corresponds to NCII content.
    """

    BASE_URL: t.ClassVar[str] = "https://api.stopncii.org/v1"

    DEFAULT_START_TIME: t.ClassVar[int] = 10

    def __init__(
        self,
        subscription_key: str,
        fetch_function_key: str,
        additional_function_keys: t.Optional[t.Dict[StopNCIIEndpoint, str]] = None,
        base_url_override: t.Optional[str] = None,
    ) -> None:
        self._function_keys = dict(additional_function_keys or {})
        self._function_keys[StopNCIIEndpoint.FetchHashes] = fetch_function_key
        self._subscription_key = subscription_key

        self._base_url = base_url_override or self.BASE_URL

    def _get_session(self, endpoint: StopNCIIEndpoint):
        """
        Custom requests sesson

        Ideally, should be used within a context manager:
        ```
        with self._get_session() as session:
            session.get()...
        ```

        If using without a context manager, ensure you end up calling close() on
        the returned value.
        """
        function_key = self._function_keys.get(endpoint)
        if not function_key:
            raise ValueError(
                f"You don't have a function key for the endpoint {endpoint}"
            )

        session = requests.Session()
        session.headers.update(
            {
                "x-functions-key": function_key,
                "Ocp-Apim-Subscription-Key": self._subscription_key,
            }
        )
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

    def _get(self, endpoint: StopNCIIEndpoint, **params) -> t.Any:
        """
        Perform an HTTP GET request, and return the JSON response payload.

        Same timeouts and retry strategy as `_get_session` above.
        """

        url = "/".join((self._base_url, endpoint.value))
        with self._get_session(endpoint) as session:
            response = session.get(url, params=params)
            response.raise_for_status()
            return response.json()

    def _get_fetch_hashes_json(self, **params) -> t.Optional[t.Any]:
        """
        GET the FetchHashes endpoint, tolerating a malformed response body.

        The StopNCII API has been observed to return HTTP 200 with a corrupt
        JSON body for specific windows; parsing such a page crashes
        response.json() before any record-level handling can happen. Since
        an unparseable page also cannot yield nextPageToken or
        nextSetTimestamp, this returns None instead of raising, and the
        caller decides how to make progress (see fetch_hashes_iter).

        Retries once first: transient truncation heals on a second request,
        persistent corruption does not.
        """
        for attempt in range(2):
            try:
                return self._get(StopNCIIEndpoint.FetchHashes, **params)
            except JSONDecodeError as e:
                extra = ""
                doc = getattr(e, "doc", None)
                pos = getattr(e, "pos", None)
                if isinstance(doc, str) and isinstance(pos, int):
                    start = max(0, pos - 100)
                    end = min(len(doc), pos + 100)
                    extra = " Nearby body: %r." % doc[start:end]
                logging.error(
                    "StopNCII FetchHashes returned a malformed JSON body "
                    "(params: %s, attempt %d/2), err: %s.%s "
                    "Please open an issue if you see this logging statement.",
                    params,
                    attempt + 1,
                    e,
                    extra,
                )
        return None

    def _post(self, endpoint: StopNCIIEndpoint, *, json=None) -> t.Any:
        """
        Perform an HTTP POST request, and return the JSON response payload.

        No timeout or retry strategy.
        """

        url = "/".join((self._base_url, endpoint.value))
        with self._get_session(endpoint) as session:
            response = session.post(url, json=json)
            response.raise_for_status()
            return response.json()

    def fetch_hashes(
        self,
        *,
        page_size: int = 800,
        start_timestamp: int = DEFAULT_START_TIME,
        next_page: str = "",
    ) -> t.Optional[FetchHashesResponse]:
        """
        Fetch a series of update records from the hash API.

        Records represent the current snapshot of all data, so if you see
        the same SignalType+Hash in a later iteration, it should completely
        replace the previously observed record.

        Returns None if the response body could not be parsed after a
        retry - see _get_fetch_hashes_json.
        """
        params: t.Dict[str, t.Any] = {
            "startTimestamp": start_timestamp,
            "pageSize": page_size,
        }
        if next_page:
            params["nextPageToken"] = next_page
        logging.debug("StopNCII FetchHashes called: %s", params)
        json_val = self._get_fetch_hashes_json(**params)
        if json_val is None:
            return None
        logging.debug("StopNCII FetchHashes returns: %s", json_val)
        # If there is a malformed record or a change that would prevent the deserialization
        # of a record, skip over it instead of crashing. Please open an issue if you see the logging
        # statement below.
        records: t.List[StopNCIIHashRecord] = []
        for record in json_val.get("hashRecords", []):
            try:
                records.append(
                    dacite.from_dict(
                        data_class=StopNCIIHashRecord,
                        data=record,
                        config=dacite.Config(cast=[enum.Enum, set]),
                    )
                )
            except ValueError as e:
                logging.error(
                    "Convert response from JSON to Dataclass failed, err: %s, record: %s",
                    e,
                    record,
                )
        response: FetchHashesResponse = dacite.from_dict(
            data_class=FetchHashesResponse,
            data={**json_val, "hashRecords": []},
            config=dacite.Config(cast=[enum.Enum, set]),
        )
        response.hashRecords = records
        return response

    def fetch_hashes_iter(
        self, start_timestamp: int = DEFAULT_START_TIME
    ) -> t.Iterator[FetchHashesResponse]:
        """
        A simple wrapper around FetchHashes to keep fetching until complete.

        You could get the entire record stream from:
        everything = {
            (record.signalType, record.hashValue): record
            for result in api.fetch_hashes_iter()
            for record in result.hashRecords
        }

        If a page body is unparseable even after a retry, yields an empty
        FetchHashesResponse whose nextSetTimestamp is advanced by
        MALFORMED_PAGE_SKIP_SECONDS so the caller checkpoint can move past
        the corrupt window instead of stalling forever.
        """
        has_more = True
        next_page = ""
        # Last observed nextSetTimestamp (or the original start), used as the
        # base when a page is unparseable and we have to jump the window.
        skip_from = start_timestamp
        skips = 0
        while has_more:
            result = self.fetch_hashes(
                start_timestamp=start_timestamp, next_page=next_page
            )
            if result is None:
                skips += 1
                skipped_to = skip_from + MALFORMED_PAGE_SKIP_SECONDS
                now = int(time.time())
                keep_going = skips < MALFORMED_PAGE_MAX_SKIPS and skipped_to < now
                logging.error(
                    "StopNCII FetchHashes skipping malformed page window "
                    "[%s, %s); checkpoint will advance to %s. Records in "
                    "this window will not be ingested unless re-fetched "
                    "after the server-side data is fixed.",
                    skip_from,
                    skipped_to,
                    skipped_to,
                )
                yield FetchHashesResponse(
                    count=0,
                    nextPageToken=None,
                    nextSetTimestamp=skipped_to,
                    hasMoreRecords=keep_going,
                    hashRecords=[],
                )
                if not keep_going:
                    return
                start_timestamp = skipped_to
                skip_from = skipped_to
                next_page = ""
                continue
            skip_from = result.nextSetTimestamp
            skips = 0
            has_more = result.hasMoreRecords
            next_page = result.nextPageToken or ""
            yield result

    def submit_hash(
        self,
        signal_type: StopNCIISignalType,
        hash_value: str,
        tags: t.Optional[t.Set[str]] = None,
        reported_state: StopNCIICSPFeedbackValue = StopNCIICSPFeedbackValue.Blocked,
    ) -> None:
        """Convenience accessor for reporting a single hash"""
        self.submit_hashes(
            {
                (signal_type, hash_value): StopNCIICSPFeedback(
                    reported_state, tags or set()
                )
            }
        )

    def submit_hashes(
        self, hashes: t.Dict[t.Tuple[StopNCIISignalType, str], StopNCIICSPFeedback]
    ) -> None:
        """
        Upload hashes as a CSP to StopNCII.org.

        Most hashes come from users submitting to the portal, but the API
        allows for CSPs to source their own hashes as well.
        """
        now = int(time.time())
        records = []
        for (signal_type, hashValue), feedback in hashes.items():
            records.append(
                {
                    "lastModtimestamp": now,
                    "signalType": str(signal_type),
                    "hashValue": hashValue,
                    "CSPFeedbacks": [feedback.as_dict_for_post()],
                }
            )
        payload = {"count": len(hashes), "hashRecords": records}
        self._post(StopNCIIEndpoint.SubmitHashes, json=payload)

    def submit_feedback(
        self,
        signal_type: StopNCIISignalType,
        hash_value: str,
        feedback: StopNCIICSPFeedbackValue,
        tags: t.Optional[t.Set[str]] = None,
    ) -> None:
        """
        Convenience function for submitting feedback for a single hash.

        Note that even a single hash may correspond to multiple cases.
        """
        self.submit_feedbacks(
            {(signal_type, hash_value): StopNCIICSPFeedback(feedback, tags or set())}
        )

    def submit_feedbacks(
        self, feedbacks: t.Dict[t.Tuple[StopNCIISignalType, str], StopNCIICSPFeedback]
    ) -> None:
        """Submit feedback on multiple hashes"""
        now = int(time.time())
        # Now for the fun hacky part, convert to expected format
        feedback_dicts = []
        for (_signal_type, hashValue), feedback in feedbacks.items():
            # Why isn't signalType used here?
            fb_dict = feedback.as_dict_for_post()
            fb_dict["hashValue"] = hashValue
            feedback_dicts.append(fb_dict)
        payload = {"count": len(feedbacks), "hashFeedbacks": feedback_dicts}
        self._post(StopNCIIEndpoint.SubmitFeedback, json=payload)


def is_valid_key(key: str) -> bool:
    """
    Returns true if the string looks like a valid stopncii key
    """
    return bool(key)  # TODO
