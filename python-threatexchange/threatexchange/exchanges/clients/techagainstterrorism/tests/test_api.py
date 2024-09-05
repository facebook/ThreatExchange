import typing as t
import pytest
from datetime import datetime

from threatexchange.exchanges.clients.techagainstterrorism.api import (
    TATIdeology,
    TATHashListResponse,
    TATHashListAPI,
)


def mock_get_hash_list(
    ideology: str = TATIdeology._all.value,
) -> t.Union[TATHashListResponse, dict[str, str]]:

    if ideology not in TATIdeology._value2member_map_:
        return {
            "error": f"400 Client Error: Bad Request for url: https://test/api/hash-list/{ideology}"
        }

    return TATHashListResponse(
        file_url=f"https://hash-list.s3.com/19700101_{ideology}_hashes.json",
        file_name=f"19790101_{ideology}_hashes.json",
        created_on=datetime.strptime("2021-08-01T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ"),
        total_hashes=1000,
        ideology=ideology,
    )


def mock_authenticate() -> str | None:
    return "mock_token"


@pytest.fixture
def api(monkeypatch) -> TATHashListAPI:
    api_instance = TATHashListAPI(username="valid_user", password="valid_pass")
    monkeypatch.setattr(api_instance, "authenticate", mock_authenticate)
    monkeypatch.setattr(api_instance, "get_hash_list", mock_get_hash_list)
    return api_instance


def test_get_islamist_hash_list(api: TATHashListAPI) -> None:
    response = api.get_hash_list(ideology=TATIdeology.islamist.value)

    assert response == TATHashListResponse(
        file_url=f"https://hash-list.s3.com/19700101_islamist_hashes.json",
        file_name=f"19790101_islamist_hashes.json",
        created_on=datetime.strptime("2021-08-01T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ"),
        total_hashes=1000,
        ideology=TATIdeology.islamist.value,
    )


def test_get_far_right_hash_list(api: TATHashListAPI) -> None:
    response = api.get_hash_list(ideology=TATIdeology.far_right.value)

    assert response == TATHashListResponse(
        file_url=f"https://hash-list.s3.com/19700101_far-right_hashes.json",
        file_name=f"19790101_far-right_hashes.json",
        created_on=datetime.strptime("2021-08-01T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ"),
        total_hashes=1000,
        ideology=TATIdeology.far_right.value,
    )


def test_get_all_hash_list(api: TATHashListAPI) -> None:
    response = api.get_hash_list(TATIdeology._all.value)

    assert response == TATHashListResponse(
        file_url=f"https://hash-list.s3.com/19700101_all_hashes.json",
        file_name=f"19790101_all_hashes.json",
        created_on=datetime.strptime("2021-08-01T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ"),
        total_hashes=1000,
        ideology=TATIdeology._all.value,
    )


def test_get_default_hash_list(api: TATHashListAPI) -> None:
    response = api.get_hash_list()

    assert response == TATHashListResponse(
        file_url=f"https://hash-list.s3.com/19700101_all_hashes.json",
        file_name=f"19790101_all_hashes.json",
        created_on=datetime.strptime("2021-08-01T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ"),
        total_hashes=1000,
        ideology=TATIdeology._all.value,
    )


def test_incorrect_ideology_hash_list(api: TATHashListAPI) -> None:
    response = api.get_hash_list("invalid_ideology")
    assert response == {
        "error": "400 Client Error: Bad Request for url: https://test/api/hash-list/invalid_ideology"
    }
