# Copyright (c) Meta Platforms, Inc. and affiliates.
import pytest
import mock

from pytx import access_token
from pytx.errors import pytxAccessTokenError
from pytx.vocabulary import ThreatExchange as te


class TestAccessToken:
    def verify_token(self, expected_token):
        assert expected_token == access_token.get_access_token()

    @mock.patch("pytx.access_token._find_token_file", return_value=None)
    def test_no_token(self, mock_patch):
        with pytest.raises(pytxAccessTokenError):
            access_token.access_token()

    @mock.patch("pytx.access_token._find_token_file", return_value=None)
    def test_only_app_id(self, mock_patch):
        with pytest.raises(pytxAccessTokenError):
            access_token.access_token(app_id="app_id")

    @mock.patch("pytx.access_token._find_token_file", return_value=None)
    def test_only_app_secret(self, mock_patch):
        with pytest.raises(pytxAccessTokenError):
            access_token.access_token(app_secret="app_secret")

    @mock.patch("pytx.access_token._find_token_file", return_value=None)
    def test_app_id_and_secret(self, mock_patch):
        expected_token = "app_id|app_secret"
        access_token.access_token(app_id="app_id", app_secret="app_secret")
        self.verify_token(expected_token)

    @mock.patch(
        "pytx.access_token._find_token_file", return_value="/foobar/mocked/away"
    )
    @mock.patch("pytx.access_token._read_token_file", return_value="app_id|app_secret")
    def test_implicit_token_file(self, mock_patch, mock_patch_two):
        expected_token = "app_id|app_secret"
        access_token.access_token(token_file="/foobar/mocked/away")
        self.verify_token(expected_token)

    @mock.patch("pytx.access_token._find_token_file", return_value=None)
    @mock.patch("pytx.access_token._read_token_file", return_value="app_id|app_secret")
    def test_explicit_token_file(self, mock_patch, mock_patch_two):
        expected_token = "app_id|app_secret"
        access_token.access_token(token_file="/foobar/mocked/away")
        self.verify_token(expected_token)

    def test_single_env_var(self, monkeypatch):
        expected_token = "app_id|app_secret"

        monkeypatch.setenv(te.TX_ACCESS_TOKEN, expected_token)
        access_token.access_token()
        self.verify_token(expected_token)

    def test_double_env_var(self, monkeypatch):
        expected_token = "app_id|app_secret"

        monkeypatch.setenv(te.TX_APP_ID, "app_id")
        monkeypatch.setenv(te.TX_APP_SECRET, "app_secret")
        access_token.access_token()
        self.verify_token(expected_token)
