from mock import patch
import pytest

from pytx import access_token
from pytx.errors import pytxInitError
from pytx.vocabulary import ThreatExchange as te


class TestInit:

    def verify_token(self, expected_token):
        assert expected_token == access_token.__ACCESS_TOKEN__

    def test_no_params(self):
        with pytest.raises(pytxInitError):
            access_token.init()

    def test_only_app_id(self):
        with pytest.raises(pytxInitError):
            access_token.init(app_id='app_id')

    def test_only_app_secret(self):
        with pytest.raises(pytxInitError):
            access_token.init(app_secret='app_secret')

    def test_app_id_and_secret(self):
        expected_token = 'app_id|app_secret'

        access_token.init(app_id='app_id', app_secret='app_secret')
        self.verify_token(expected_token)

    def verify_token_file(self, expected_token, file_contents):
        with patch('pytx.access_token._read_token_file', return_value=file_contents):
            access_token.init(token_file='/foobar/mocked/away')
            self.verify_token(expected_token)

    def test_1_line_token_file(self):
        expected_token = 'app_id|app_secret'
        file_contents = ['app_id|app_secret']
        self.verify_token_file(expected_token, file_contents)

    def test_2_line_token_file(self):
        expected_token = 'app_id|app_secret'
        file_contents = ['app_id', 'app_secret']
        self.verify_token_file(expected_token, file_contents)

    def test_3_line_token_file(self):
        expected_token = 'app_id|app_secret'
        file_contents = ['app_id', 'app_secret', 'whoops_extra_line']
        with pytest.raises(pytxInitError):
            self.verify_token_file(expected_token, file_contents)

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
