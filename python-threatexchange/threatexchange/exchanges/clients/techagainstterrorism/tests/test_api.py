# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t
import pytest

from threatexchange.exchanges.clients.techagainstterrorism.api import (
    TATHashListAPI,
    TATHashListResponse,
    TATHashListEntry,
    TATIdeology,
)


mock_hashes: t.List[TATHashListEntry] = [
    TATHashListEntry(
        hash_digest="123abc",
        algorithm="MD5",
        ideology=TATIdeology.islamist,
        file_type="png",
        deleted=False,
        updated_on=1704901040.222779,
        id=2819,
    ),
    TATHashListEntry(
        hash_digest="456def",
        algorithm="SHA256",
        ideology=TATIdeology.far_right,
        file_type="jpg",
        deleted=False,
        updated_on=1704901040.24492,
        id=2820,
    ),
    TATHashListEntry(
        hash_digest="789ghi",
        algorithm="MD5",
        ideology=TATIdeology.islamist,
        file_type="gif",
        deleted=True,
        updated_on=1704901040.25555,
        id=2821,
    ),
]


def mock_fetch_hashes(after: t.Optional[str]) -> TATHashListResponse:

    return TATHashListResponse(
        count=100,
        next="http://test-hash-list.com",
        previous=None,
        checkpoint="1724856487.709035,10594",
        results=mock_hashes,
    )


def mock_fetch_hashes_iter(checkpoint: str) -> t.Iterator[TATHashListResponse]:
    for i in range(2):
        yield mock_fetch_hashes(checkpoint)


def mock_get_auth_token() -> str:
    return "mock_token"


@pytest.fixture
def api(monkeypatch) -> TATHashListAPI:
    api_instance = TATHashListAPI(username="valid_user", password="valid_pass")
    monkeypatch.setattr(api_instance, "get_auth_token", mock_get_auth_token)
    monkeypatch.setattr(api_instance, "fetch_hashes", mock_fetch_hashes)
    monkeypatch.setattr(api_instance, "fetch_hashes_iter", mock_fetch_hashes_iter)

    return api_instance


def test_fetch_hashes(api: TATHashListAPI) -> None:
    response = api.fetch_hashes(after="")

    assert response == TATHashListResponse(
        count=100,
        next="http://test-hash-list.com",
        previous=None,
        checkpoint="1724856487.709035,10594",
        results=mock_hashes,
    )


def test_fetch_hashes_iter(api: TATHashListAPI) -> None:
    for i, response in enumerate(api.fetch_hashes_iter(checkpoint="")):
        assert response == TATHashListResponse(
            count=100,
            next="http://test-hash-list.com",
            previous=None,
            checkpoint="1724856487.709035,10594",
            results=mock_hashes,
        )
