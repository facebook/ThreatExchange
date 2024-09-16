# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t
import pytest

from threatexchange.exchanges.clients.techagainstterrorism.api import (
    TATIdeology,
    TATHashListAPI,
)


def mock_get_hash_list(
    ideology: str = TATIdeology._all.value,
) -> t.Optional[t.List[t.Dict[str, str]]]:

    return [
        {
            "hash_digest": "12345abcde",
            "algorithim": "MD5",
            "ideology": ideology,
            "file_type": "jpg",
        },
        {
            "hash_digest": "12345abcde",
            "algorithim": "MD5",
            "ideology": ideology,
            "file_type": "jpg",
        },
        {
            "hash_digest": "12345abcde",
            "algorithim": "MD5",
            "ideology": ideology,
            "file_type": "jpg",
        },
    ]


def mock_get_auth_token() -> str:
    return "mock_token"


@pytest.fixture
def api(monkeypatch) -> TATHashListAPI:
    api_instance = TATHashListAPI(username="valid_user", password="valid_pass")
    monkeypatch.setattr(api_instance, "get_auth_token", mock_get_auth_token)
    monkeypatch.setattr(api_instance, "get_hash_list", mock_get_hash_list)
    return api_instance


def test_get_islamist_hash_list(api: TATHashListAPI) -> None:
    response = api.get_hash_list(ideology=TATIdeology.islamist.value)

    assert response == [
        {
            "hash_digest": "12345abcde",
            "algorithim": "MD5",
            "ideology": "islamist",
            "file_type": "jpg",
        },
        {
            "hash_digest": "12345abcde",
            "algorithim": "MD5",
            "ideology": "islamist",
            "file_type": "jpg",
        },
        {
            "hash_digest": "12345abcde",
            "algorithim": "MD5",
            "ideology": "islamist",
            "file_type": "jpg",
        },
    ]


def test_get_far_right_hash_list(api: TATHashListAPI) -> None:
    response = api.get_hash_list(ideology=TATIdeology.far_right.value)

    assert response == [
        {
            "hash_digest": "12345abcde",
            "algorithim": "MD5",
            "ideology": "far-right",
            "file_type": "jpg",
        },
        {
            "hash_digest": "12345abcde",
            "algorithim": "MD5",
            "ideology": "far-right",
            "file_type": "jpg",
        },
        {
            "hash_digest": "12345abcde",
            "algorithim": "MD5",
            "ideology": "far-right",
            "file_type": "jpg",
        },
    ]


def test_get_all_hash_list(api: TATHashListAPI) -> None:
    response = api.get_hash_list(TATIdeology._all.value)

    assert response == [
        {
            "hash_digest": "12345abcde",
            "algorithim": "MD5",
            "ideology": "all",
            "file_type": "jpg",
        },
        {
            "hash_digest": "12345abcde",
            "algorithim": "MD5",
            "ideology": "all",
            "file_type": "jpg",
        },
        {
            "hash_digest": "12345abcde",
            "algorithim": "MD5",
            "ideology": "all",
            "file_type": "jpg",
        },
    ]


def test_get_default_hash_list(api: TATHashListAPI) -> None:
    response = api.get_hash_list()

    assert response == [
        {
            "hash_digest": "12345abcde",
            "algorithim": "MD5",
            "ideology": "all",
            "file_type": "jpg",
        },
        {
            "hash_digest": "12345abcde",
            "algorithim": "MD5",
            "ideology": "all",
            "file_type": "jpg",
        },
        {
            "hash_digest": "12345abcde",
            "algorithim": "MD5",
            "ideology": "all",
            "file_type": "jpg",
        },
    ]
