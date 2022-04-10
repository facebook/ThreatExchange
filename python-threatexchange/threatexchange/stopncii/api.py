# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""Simple implementation for the StopNCII REST API"""

from dataclasses import dataclass, asdict, field
import enum
import logging
import time
import typing as t

import dacite
import requests
from requests.packages.urllib3.util.retry import Retry

# Maybe move to a common library someday
from threatexchange.fb_threatexchange.api import TimeoutHTTPAdapter


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
    """"""

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

    source: str  # Name of the Content Service Provider (CSP)
    feedbackValue: StopNCIICSPFeedbackValue  # What the feedback is
    tags: t.Set[str]  # Unstructured additional tags


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
    nextPageToken: str  # Cursor for paginating, not valid over long periods of time
    nextSetTimestamp: int  # The best timestamp to use to store as a checkpoint
    hasMoreRecords: bool  # If the cursor is fully played out
    hashRecords: t.List[StopNCIIHashRecord]  # The records


class StopNCIIAPI:
    """
    A wrapper around the StopNCII.org hash exchange API.

    Hashes are submitted by individual people to the portal at StopNCII.org,
    and Content Service Providers (CSPs), such as social networks, can provide
    feedback on the hashes on whether they are able to verify that the content
    corresponds to NCII content.
    """

    BASE_URL: t.ClassVar[str] = "https://api.stopncii.org/"
    API_VERSION: t.ClassVar[str] = "v1"

    DEFAULT_START_TIMESTAMP: t.ClassVar[int] = 10
    PAGE_SIZE: t.ClassVar[int] = 800

    def __init__(self, function_key: str, subscription_key: str) -> None:
        self._auth_headers = {
            "x-functions-key": function_key,
            "Ocp-Apim-Subscription-Key": subscription_key,
        }

    def _get_session(self):
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
        session = requests.Session()
        session.headers.update(self._auth_headers)
        session.mount(
            self.BASE_URL,
            adapter=TimeoutHTTPAdapter(
                timeout=60,
                max_retries=Retry(
                    total=4,
                    status_forcelist=[429, 500, 502, 503, 504],
                    allowed_methods=["HEAD", "GET", "OPTIONS"],
                    backoff_factor=0.2,  # ~1.5 seconds of retries
                ),
            ),
        )
        return session

    def _get(self, endpoint: str, **json) -> t.Any:
        """
        Perform an HTTP GET request, and return the JSON response payload.
        Same timeouts and retry strategy as `_get_session` above.
        """

        url = "/".join((self.BASE_URL, self.API_VERSION, endpoint))
        with self._get_session() as session:
            response = session.get(url, json=json)
            response.raise_for_status()
            return response.json()

    def _post(self, endpoint: str, *, json=None, params=None) -> t.Any:
        """
        Perform an HTTP GET request, and return the JSON response payload.
        Same timeouts and retry strategy as `_get_session` above.
        """

        url = "/".join((self.BASE_URL, self.API_VERSION, endpoint))
        with self._get_session() as session:
            response = session.post(url, json=json, params=params or {})
            response.raise_for_status()
            return response.json()

    def fetch_hashes(
        self, *, start_timestamp: int = None, next_page: str = None
    ) -> FetchHashesResponse:
        """
        Fetch a series of update records from the hash API.

        Records represent the current snapshot of all data, so if you see
        the same SignalType+Hash in a later iteration, it should completely
        replace the previously observed record.
        """
        if start_timestamp is None:
            start_timestamp = self.DEFAULT_START_TIMESTAMP
        params: t.Dict[str, t.Any] = {"startTimestamp": start_timestamp}
        if next_page is not None:
            params["nextPageToken"] = next_page
        json_val = self._get("FetchHashes", **params)
        logging.debug("StopNCII FetchHashes returns: %s", json_val)
        return dacite.from_dict(
            data_class=FetchHashesResponse,
            data=json_val,
            config=dacite.Config(cast=[enum.Enum, set]),
        )

    def fetch_hashes_iter(
        self, start_timestamp: int = None
    ) -> t.Iterator[FetchHashesResponse]:
        """
        A simple wrapper around FetchHashes to keep fetching until complete.

        You could get the entire record stream from:
        everything = {
            (record.signalType, record.hashValue): record
            for result in api.fetch_hashes_iter()
            for record in result.hashRecords
        }

        """
        has_more = True
        next_page = None
        while has_more:
            result = self.fetch_hashes(
                start_timestamp=start_timestamp, next_page=next_page
            )
            has_more = result.hasMoreRecords
            next_page = result.nextPageToken
            yield result

    def submit_feedback(
        self,
        signal_type: StopNCIISignalType,
        hash_value: str,
        feedback: StopNCIICSPFeedback,
    ) -> None:
        """
        Convenience accessor for submitting feedback for a single hash.

        Note that even a single hash may correspond to multiple cases.
        """
        self.submit_feedbacks({(signal_type, hash_value): feedback})

    def submit_feedbacks(
        self, feedbacks: t.Dict[t.Tuple[StopNCIISignalType, str], StopNCIICSPFeedback]
    ) -> None:
        """Submit feedback on multiple hashes"""
        now = int(time.time())
        # Now for the fun hacky part, convert to expected format
        records = []
        for (signal_type, hashValue), feedback in feedbacks.items():
            fb_dict = asdict(feedback)
            fb_dict["tags"] = list(fb_dict["tags"])  # Convert from set
            fb_dict["feedbackValue"] = str(
                fb_dict["feedbackValue"]
            )  # Convert from enum

            records.append(
                {
                    "lastModtimestamp": now,
                    "signalType": str(signal_type),
                    "hashValue": hashValue,
                    "CSPFeedbacks": [fb_dict],
                }
            )
        payload = {"count": len(feedbacks), "hashRecords": records}
        self._post("SubmitHashes", json=payload)
