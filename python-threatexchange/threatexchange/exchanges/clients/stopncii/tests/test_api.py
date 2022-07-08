import pytest
from threatexchange.exchanges.clients.stopncii.api import (
    StopNCIIAPI,
    StopNCIICaseStatus,
    StopNCIICSPFeedbackValue,
    StopNCIIEndpoint,
    StopNCIIHashRecord,
    StopNCIISignalType,
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
