# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t
from unittest.mock import MagicMock
import pytest

from threatexchange.exchanges.clients.techagainstterrorism.api import (
    TATIdeology,
    TATHashListAPI,
)


def mock_fetch_hashes(after: str) -> t.Optional[t.List[t.Dict[str, str]]]:
    return {
        "count": 100,
        "next": "http://dev.terrorismanalytics.org/hash-list/v2/all?limit=1000&offset=1000&order=asc",
        "previous": None,
        "checkpoint": "1724856487.709035,10594",
        "results": [
            {
                "hash_digest": "123abc",
                "algorithm": "MD5",
                "ideology": "Far-Right",
                "file_type": "mp4",
                "deleted": False,
                "updated_on": 1704901040.222779,
                "id": 2819,
            },
            {
                "hash_digest": "456def",
                "algorithm": "SHA256",
                "ideology": "Islamist",
                "file_type": "mp4",
                "deleted": False,
                "updated_on": 1704901040.24492,
                "id": 2820,
            },
            {
                "hash_digest": "456def",
                "algorithm": "PDQ",
                "ideology": "Islamist",
                "file_type": "png",
                "deleted": False,
                "updated_on": 1704901040.24496,
                "id": 2821,
            },
        ],
    }


def mock_get_auth_token() -> str:
    return "mock_token"


@pytest.fixture
def api(monkeypatch) -> TATHashListAPI:
    api_instance = TATHashListAPI(username="valid_user", password="valid_pass")
    monkeypatch.setattr(api_instance, "get_auth_token", mock_get_auth_token)
    monkeypatch.setattr(api_instance, "fetch_hashes", mock_fetch_hashes)
    return api_instance


def test_fetch_hashes(api: TATHashListAPI) -> None:
    response = api.fetch_hashes(after="")

    assert response == {
        "count": 100,
        "next": "http://dev.terrorismanalytics.org/hash-list/v2/all?limit=1000&offset=1000&order=asc",
        "previous": None,
        "checkpoint": "1724856487.709035,10594",
        "results": [
            {
                "hash_digest": "123abc",
                "algorithm": "MD5",
                "ideology": "Far-Right",
                "file_type": "mp4",
                "deleted": False,
                "updated_on": 1704901040.222779,
                "id": 2819,
            },
            {
                "hash_digest": "456def",
                "algorithm": "SHA256",
                "ideology": "Islamist",
                "file_type": "mp4",
                "deleted": False,
                "updated_on": 1704901040.24492,
                "id": 2820,
            },
            {
                "hash_digest": "789ghi",
                "algorithm": "PDQ",
                "ideology": "Islamist",
                "file_type": "png",
                "deleted": False,
                "updated_on": 1704901040.24496,
                "id": 2821,
            },
        ],
    }


def test_fetch_hashes_iter(api: TATHashListAPI) -> None:
    mock_response_1 = {
        "next": "next_page_token_1",
        "checkpoint": "checkpoint_1",
        "results": [
            {
                "hash_digest": "123abc",
                "algorithm": "MD5",
                "ideology": "Far-Right",
                "file_type": "png",
                "deleted": False,
                "updated_on": 1704901040.222779,
                "id": 2819,
            },
            {
                "hash_digest": "456def",
                "algorithm": "SHA256",
                "ideology": "Islamist",
                "file_type": "png",
                "deleted": False,
                "updated_on": 1704901040.24492,
                "id": 2820,
            },
        ],
    }
    mock_response_2 = {
        "next": None,
        "checkpoint": "checkpoint_2",
        "results": [
            {
                "hash_digest": "789ghi",
                "algorithm": "MD5",
                "ideology": "Far-Right",
                "file_type": "png",
                "deleted": False,
                "updated_on": 1704901040.222779,
                "id": 2821,
            },
        ],
    }

    api.fetch_hashes = MagicMock(side_effect=[mock_response_1, mock_response_2])

    results = list(api.fetch_hashes_iter("initial_checkpoint"))

    assert len(results) == 2
    assert results[0] == mock_response_1
    assert results[1] == mock_response_2

    api.fetch_hashes.assert_any_call(after="initial_checkpoint")
    api.fetch_hashes.assert_any_call(after="checkpoint_1")
