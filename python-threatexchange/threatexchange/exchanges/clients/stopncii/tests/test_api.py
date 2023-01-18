# Copyright (c) Meta Platforms, Inc. and affiliates.

import pytest
import typing as t
from threatexchange.exchanges.clients.stopncii.api import (
    StopNCIIAPI,
    StopNCIICaseStatus,
    StopNCIICSPFeedbackValue,
    StopNCIIEndpoint,
    StopNCIIHashRecord,
    StopNCIISignalType,
    StopNCIICSPFeedback,
)

PAGE_TOKEN = (
    "W3siY29tcG9zaXRlVG9rZW4iOnsidG9rZW4iOiIrUklEOn4xMnRWQUo4SzU2Y0NB"
    "QUFBQUFBQUFBPT0jUlQ6MSNUUkM6MiNSVEQ6SFBKSm1LVDF1WnFsQkJuR3lOU09C"
    "TUhaRytHL1FBPT0jSVNWOjIjSUVPOjY1NTY3"
)


def mock_get_impl(endpoint: str, **json):
    assert endpoint == StopNCIIEndpoint.FetchHashes

    if json.get("nextPageToken") != PAGE_TOKEN:
        return {
            "count": 2,
            "nextSetTimestamp": 1625175071,
            "nextPageToken": PAGE_TOKEN,
            "hasMoreRecords": True,
            "hashRecords": [
                {
                    "lastModtimestamp": 1625167804,
                    "hashValue": "2afc4a5c09628a7961c14d436493bba66b89b831453baa1d556ba385554daa82",
                    "hashStatus": "Received",
                    "caseNumbers": {
                        "27664732-76e1-4a17-8099-455798e67022": "Received",
                        "a2696edf-1237-4eb8-a9c1-cd8ee6c055e5": "Received",
                        "9fbb73d7-c177-4ed2-b4e8-0050b72decd0": "Received",
                        "bd2bff7c-8160-4615-8dce-38c2f066d1ac": "Received",
                    },
                    "signalType": "ImagePDQ",
                },
                {
                    "lastModtimestamp": 1625167844,
                    "hashValue": "79e07de27d7295339435d63cd31cf35a7bfa29eb2885008500a588a5ea3ae75a",
                    "hashStatus": "Received",
                    "caseNumbers": {"bd2bff7c-8160-4615-8dce-38c2f066d1ac": "Received"},
                    "signalType": "ImagePDQ",
                },
            ],
        }
    return {
        "count": 1,
        "nextSetTimestamp": 1625167824,
        "nextPageToken": PAGE_TOKEN[:-1] + "4",
        "hasMoreRecords": False,
        "hashRecords": [
            {
                "lastModtimestamp": 1625175071,
                "hashValue": "9def0b7dafa86a1c90f2abd78e79ceb25ec3d1a4b3d4bc7a4354baf7717ea038",
                "hashStatus": "Active",
                "caseNumbers": {"cc592711-7068-442f-b5d2-24d50d389751": "Active"},
                "signalType": "ImagePDQ",
                "CSPFeedbacks": [
                    {
                        "source": "Facebook",
                        "feedbackValue": "Blocked",
                        "tags": ["Nude", "Objectionable"],
                    }
                ],
            },
        ],
    }


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch):
    api = StopNCIIAPI("", "")
    monkeypatch.setattr(api, "_get", mock_get_impl)
    return api


def assert_first_record(record: StopNCIIHashRecord) -> None:
    assert record.lastModtimestamp == 1625167804
    assert record.signalType == StopNCIISignalType.ImagePDQ
    assert (
        record.hashValue
        == "2afc4a5c09628a7961c14d436493bba66b89b831453baa1d556ba385554daa82"
    )
    assert record.hashStatus == StopNCIICaseStatus.Received
    assert len(record.caseNumbers) == 4
    assert all(c == StopNCIICaseStatus.Received for c in record.caseNumbers.values())
    assert len(record.CSPFeedbacks) == 0


def assert_second_record(record: StopNCIIHashRecord) -> None:
    assert record.lastModtimestamp == 1625167844
    assert record.signalType == StopNCIISignalType.ImagePDQ
    assert (
        record.hashValue
        == "79e07de27d7295339435d63cd31cf35a7bfa29eb2885008500a588a5ea3ae75a"
    )
    assert record.hashStatus == StopNCIICaseStatus.Received
    assert len(record.caseNumbers) == 1
    assert record.caseNumbers == {
        "bd2bff7c-8160-4615-8dce-38c2f066d1ac": StopNCIICaseStatus.Received
    }
    assert len(record.CSPFeedbacks) == 0


def assert_third_record(record: StopNCIIHashRecord) -> None:
    assert record.lastModtimestamp == 1625175071
    assert record.signalType == StopNCIISignalType.ImagePDQ
    assert (
        record.hashValue
        == "9def0b7dafa86a1c90f2abd78e79ceb25ec3d1a4b3d4bc7a4354baf7717ea038"
    )
    assert record.hashStatus == StopNCIICaseStatus.Active
    assert len(record.caseNumbers) == 1
    assert record.caseNumbers == {
        "cc592711-7068-442f-b5d2-24d50d389751": StopNCIICaseStatus.Active
    }

    assert len(record.CSPFeedbacks) == 1
    feedback = record.CSPFeedbacks[0]
    assert feedback.source == "Facebook"
    assert feedback.feedbackValue == StopNCIICSPFeedbackValue.Blocked
    assert feedback.tags == {"Nude", "Objectionable"}


def test_mocked_get_hashes(api: StopNCIIAPI):
    result = api.fetch_hashes()

    assert result.count == 2
    assert result.nextSetTimestamp == 1625175071
    assert result.hasMoreRecords is True
    assert result.nextPageToken == PAGE_TOKEN
    assert len(result.hashRecords) == 2

    one, two = result.hashRecords
    assert_first_record(one)
    assert_second_record(two)

    second_result = api.fetch_hashes(next_page=result.nextPageToken)

    assert second_result.count == 1
    assert second_result.nextSetTimestamp == 1625167824
    assert second_result.hasMoreRecords is False
    assert second_result.nextPageToken != PAGE_TOKEN
    assert len(second_result.hashRecords) == 1
    assert_third_record(second_result.hashRecords[0])


def test_mocked_get_hashes_iter(api: StopNCIIAPI):
    it = api.fetch_hashes_iter()
    as_list = list(it)
    assert len(as_list) == 2

    all_updates = [
        record for result in api.fetch_hashes_iter() for record in result.hashRecords
    ]
    assert len(all_updates) == 3
    one, two, three = all_updates
    assert_first_record(one)
    assert_second_record(two)
    assert_third_record(three)


def mock_get_impl_error_enum(endpoint: str, **json):
    assert endpoint == StopNCIIEndpoint.FetchHashes
    return {
        "count": 3,
        "nextSetTimestamp": 1625167824,
        "nextPageToken": PAGE_TOKEN[:-1] + "4",
        "hasMoreRecords": False,
        "hashRecords": [
            {
                "lastModtimestamp": 1625175071,
                "hashValue": "9def0b7dafa86a1c90f2abd78e79ceb25ec3d1a4b3d4bc7a4354baf7717ea038",
                "hashStatus": "Active",
                "caseNumbers": {"cc592711-7068-442f-b5d2-24d50d389751": "Active"},
                "signalType": "ImagePDQ",
                "CSPFeedbacks": [
                    {
                        "source": "Facebook",
                        "feedbackValue": "Blocked",
                        "tags": ["Nude", "Objectionable"],
                    }
                ],
            },
            {
                "lastModtimestamp": 1625175071,
                "hashValue": "9def0b7dafa86a1c90f2abd78e79ceb25ec3d1a4b3d4bc7a4354baf7717ea038",
                "hashStatus": "Active",
                "caseNumbers": {"cc592711-7068-442f-b5d2-24d50d389751": "Active"},
                "signalType": "ImagePDQ",
                "CSPFeedbacks": [
                    {
                        "source": "Facebook",
                        "feedbackValue": "RandomFeedbackValue",
                        "tags": ["Nude", "Objectionable"],
                    }
                ],
            },
            {
                "lastModtimestamp": 1661426988,
                "hashValue": "95d087d087f8f41cf00771c707f713c7675d07f8c618f00ef00f07f307e37087",
                "hashStatus": "Active",
                "caseNumbers": {
                    "bce008ff-e114-4815-9de8-8f4a50bfd471": "Active",
                    "df018705-fb65-4481-a036-cce0ab02168a": "Active",
                    "504b123a-0fd9-4b95-b7ad-42abf88a1d09": "Received",
                    "ab2754fb-836d-4947-b633-e0c6c7d55255": "Active",
                    "cfaa8342-4f7e-4f5f-88bd-9fd083eafe57": "Active",
                },
                "signalType": "ImagePDQ",
                "hashRegions": ["UK"],
                "CSPFeedbacks": [
                    {
                        "source": "TikTok",
                        "feedbackValue": "Undefined",
                        "tags": ["Tag-One", "Tag-eight"],
                    },
                    {
                        "source": "Twitter",
                        "feedbackValue": "Undefined",
                        "tags": ["Tag-One", "Tag-eight"],
                    },
                ],
            },
        ],
    }


def test_mocked_get_hashes_with_undefined_enum(monkeypatch: pytest.MonkeyPatch):
    error_enum_api = StopNCIIAPI("", "")
    monkeypatch.setattr(error_enum_api, "_get", mock_get_impl_error_enum)
    result = error_enum_api.fetch_hashes()
    assert result.count == 3
    assert len(result.hashRecords) == 1  # since only one record has valid feedbackValue


def mock_feedbacks() -> t.Dict[t.Tuple[StopNCIISignalType, str], StopNCIICSPFeedback]:
    hash_str_1 = "2afc4a5c09628a7961c14d436493bba66b89b831453baa1d556ba385554daa82"
    hash_str_2 = "79e07de27d7295339435d63cd31cf35a7bfa29eb2885008500a588a5ea3ae75a"
    return {
        (StopNCIISignalType.ImagePDQ, hash_str_1): StopNCIICSPFeedback(
            feedbackValue=StopNCIICSPFeedbackValue.Deleted,
            source="facebook",
            tags={"Adult", "Nude"},
        ),
        (StopNCIISignalType.ImagePDQ, hash_str_2): StopNCIICSPFeedback(
            feedbackValue=StopNCIICSPFeedbackValue.Blocked,
            source="snapchat",
            tags={"Nude"},
        ),
    }


def mock_submit_feedback_post_impl(endpoint: str, json):
    # since tags field is `set`, may not inorder, needs to sort in advance
    json["hashFeedbacks"][0]["tags"].sort()
    desired_json = {
        "count": 2,
        "hashFeedbacks": [
            {
                "tags": ["Adult", "Nude"],
                "feedbackValue": "Deleted",
                "hashValue": "2afc4a5c09628a7961c14d436493bba66b89b831453baa1d556ba385554daa82",
            },
            {
                "tags": ["Nude"],
                "feedbackValue": "Blocked",
                "hashValue": "79e07de27d7295339435d63cd31cf35a7bfa29eb2885008500a588a5ea3ae75a",
            },
        ],
    }
    assert endpoint == StopNCIIEndpoint.SubmitFeedback
    assert json == desired_json


@pytest.fixture
def submit_feedback_api(monkeypatch: pytest.MonkeyPatch):
    return submit_feedback_api


def test_post_feedbacks(monkeypatch: pytest.MonkeyPatch):
    submit_feedback_api = StopNCIIAPI("", "")
    monkeypatch.setattr(submit_feedback_api, "_post", mock_submit_feedback_post_impl)
    submit_feedback_api.submit_feedbacks(mock_feedbacks())
