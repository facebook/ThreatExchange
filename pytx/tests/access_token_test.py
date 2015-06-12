from contextlib import nested
from mock import patch
import pytest

from pytx import access_token
from pytx.errors import pytxInitError
from pytx.vocabulary import ThreatExchange as te


class TestInit:

    def verify_token(self, expected_token):
        assert expected_token == access_token.get_access_token()

    def test_no_token(self):
        with nested(
            pytest.raises(pytxInitError),
            patch('pytx.access_token._find_token_file', return_value=None)
        ):
            access_token.init()

    def test_only_app_id(self):
        with nested(
            pytest.raises(pytxInitError),
            patch('pytx.access_token._find_token_file', return_value=None)
        ):
            access_token.init(app_id='app_id')

    def test_only_app_secret(self):
        with nested(
            pytest.raises(pytxInitError),
            patch('pytx.access_token._find_token_file', return_value=None)
        ):
            access_token.init(app_secret='app_secret')

    def test_app_id_and_secret(self):
        expected_token = 'app_id|app_secret'

        with patch('pytx.access_token._find_token_file', return_value=None):
            access_token.init(app_id='app_id', app_secret='app_secret')
            self.verify_token(expected_token)

    def test_implicit_token_file(self):
        expected_token = 'app_id|app_secret'
        file_contents = 'app_id|app_secret'

        with nested(
            patch('pytx.access_token._find_token_file', return_value='/foobar/mocked/away'),
            patch('pytx.access_token._read_token_file', return_value=file_contents)
        ):
            access_token.init(token_file='/foobar/mocked/away')
            self.verify_token(expected_token)

    def test_explicit_token_file(self):
        expected_token = 'app_id|app_secret'
        file_contents = 'app_id|app_secret'

        with nested(
            patch('pytx.access_token._find_token_file', return_value=None),
            patch('pytx.access_token._read_token_file', return_value=file_contents)
        ):
            access_token.init(token_file='/foobar/mocked/away')
            self.verify_token(expected_token)

    def test_single_env_var(self, monkeypatch):
        expected_token = 'app_id|app_secret'

        monkeypatch.setenv(te.TX_ACCESS_TOKEN, expected_token)
        access_token.init()
        self.verify_token(expected_token)

    def test_double_env_var(self, monkeypatch):
        expected_token = 'app_id|app_secret'

        monkeypatch.setenv(te.TX_APP_ID, 'app_id')
        monkeypatch.setenv(te.TX_APP_SECRET, 'app_secret')
        access_token.init()
        self.verify_token(expected_token)
