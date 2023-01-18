# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Typed representations (dataclasses only) for interfacing with the
API classes.

Documentation at: https://fburl.com/q7n60hjr (FB internal at this point, update when there is a public URL.)
"""

from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import typing as t


class SignalType(Enum):
    # TODO: Find where these are sourced from.
    Unknown = 0
    ImagePDQ = 1
    VideoTMK = 2
    VideoMD5 = 3
    Text = 16
    URL = 17


class CaseStatus(Enum):
    # TODO: Find where these are sourced from.
    Unknown = 0
    Received = 1
    Active = 2
    Withdrawn = 8192
    Deleted = 16384


class CSPFeedback(Enum):
    # TODO: Are there known values for these keys?
    Unknown = 0
    QualityUnknown = 1
    PendingReview = 2
    Blocked = 3
    NotBlocked = 4
    Withdrawn = 5
    Deleted = 6


@dataclass
class CSPFeedbackRecord:
    """
    Feedback about a hash record from a CSP.
    """

    # Which CSP has given this feedback?
    source: str

    # What does the CSP have to say about this hash
    feedback_value: CSPFeedback

    # What optional tags has the CSP added?
    tags: t.List[str]

    @classmethod
    def from_dict(cls, d: dict) -> "CSPFeedbackRecord":
        return cls(
            source=d.get("source", None),
            feedback_value=CSPFeedback(d.get("feedbackValue", None)),
            tags=d.get("tags", []),
        )


@dataclass
class HashRecord:
    """
    An individual record of a hash from StopNCII.
    """

    # Kind of signal? Is it a PDQ hash, an MD5 hash etc.
    signal_type: SignalType

    # Actual hash value.
    hash_value: str

    # Status of the overall case. Unclear whether this is guaranteed to be from
    # within CaseStatus
    hash_status: t.Union[str, CaseStatus]

    # The status of each case that has this hash
    case_numbers: t.Dict[str, CaseStatus]

    # The tags provided by the users, the NGO or the CSPs
    tags: t.List[str]

    # arbitrary strings indicating locations from where the hash comes.
    hash_regions: t.List[str]

    # feedback from CSPs on this hash
    csp_feedbacks: t.List[CSPFeedbackRecord]

    # When was this record last modified?
    last_modified_at: datetime

    @classmethod
    def from_dict(cls, d: dict) -> "HashRecord":
        return cls(
            signal_type=SignalType[d.get("signalType", 0)],
            hash_value=d.get("hashValue", None),
            hash_status=CaseStatus[d.get("hashStatus", None)],
            case_numbers={
                case: CaseStatus[status]
                for case, status in d.get("caseNumbers", {}).items()
            },
            tags=d.get("tags", []),
            hash_regions=d.get("hashRegions", []),
            csp_feedbacks=[
                CSPFeedbackRecord.from_dict(x) for x in d.get("CSPFeedbacks", [])
            ],
            last_modified_at=datetime.fromtimestamp(d.get("lastModtimestamp", None)),
        )


@dataclass
class HashRecordsPage:
    """
    A pagefull of hash records from StopNCII.org APIs.
    """

    # how many records in this response?
    count: int

    # Actual hash records.
    hash_records: t.List[HashRecord]

    # Use this in the next call as the query timestamp.
    next_set_timestamp: int

    # are there more records beyond this page?
    has_more_records: bool

    # Internal token that needs to be forwarded for the next page.
    next_page_token: t.Optional[str]

    @classmethod
    def from_dict(cls, d: dict) -> "HashRecordsPage":
        return cls(
            count=d.get("count", None),
            hash_records=[HashRecord.from_dict(x) for x in d.get("hashRecords", [])],
            next_set_timestamp=d.get("nextSetTimestamp", None),
            has_more_records=d.get("hasMoreRecords", None),
            next_page_token=d.get("nextPageToken", None),
        )
