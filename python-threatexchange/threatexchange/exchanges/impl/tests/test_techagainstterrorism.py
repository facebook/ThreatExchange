import pytest

from threatexchange.exchanges.clients.techagainstterrorism import api
from threatexchange.exchanges.impl.techagainstterrorism_api import (
    TATSignalExchangeAPI,
    TATCredentials,
)
from threatexchange.exchanges import fetch_state as state
from threatexchange.exchanges.collab_config import (
    CollaborationConfigWithDefaults,
)


def test_init():
    api_instance = TATSignalExchangeAPI(username="test_user", password="test_pass")
    assert api_instance.username == "test_user"
    assert api_instance.password == "test_pass"


def test_get_config_cls():
    assert TATSignalExchangeAPI.get_config_cls() == CollaborationConfigWithDefaults


def test_get_checkpoint_cls():
    assert TATSignalExchangeAPI.get_checkpoint_cls() == state.NoCheckpointing


def test_get_record_cls():
    assert TATSignalExchangeAPI.get_record_cls() == state.FetchedSignalMetadata


def test_get_credential_cls():
    assert TATSignalExchangeAPI.get_credential_cls() == TATCredentials


def test_get_name(monkeypatch):
    monkeypatch.setattr(
        "threatexchange.exchanges.impl.techagainstterrorism_api._API_NAME",
        "test_api_name",
    )
    assert TATSignalExchangeAPI.get_name() == "test_api_name"


def test_for_collab(monkeypatch):
    collab = CollaborationConfigWithDefaults(name="test_collab")
    credentials = TATCredentials(username="test_user", password="test_pass")
    monkeypatch.setattr(TATCredentials, "get", lambda *args, **kwargs: credentials)
    api_instance = TATSignalExchangeAPI.for_collab(collab)
    assert isinstance(api_instance, TATSignalExchangeAPI)
    assert api_instance.username == "test_user"
    assert api_instance.password == "test_pass"


def test_get_client(monkeypatch):
    api_instance = TATSignalExchangeAPI(username="test_user", password="test_pass")
    monkeypatch.setattr(
        api, "TATHashListAPI", lambda *args, **kwargs: "mock_client_instance"
    )
    client = api_instance.get_client()
    assert client == "mock_client_instance"


def test_fetch_iter(monkeypatch):
    api_instance = TATSignalExchangeAPI(username="test_user", password="test_pass")
    mock_client_instance = type(
        "MockClient",
        (object,),
        {"get_hash_list": lambda self: [{"id": 1, "data": "test_data"}]},
    )()
    monkeypatch.setattr(api_instance, "get_client", lambda: mock_client_instance)

    def mock_get_delta_mapping(entry):
        return (("signal_type", "signal_value"), entry)

    monkeypatch.setattr(
        "threatexchange.exchanges.impl.techagainstterrorism_api._get_delta_mapping",
        mock_get_delta_mapping,
    )

    result = list(api_instance.fetch_iter([], None))
    assert len(result) == 1
    assert isinstance(result[0], state.FetchDelta)
    assert result[0].checkpoint == state.NoCheckpointing()
    assert result[0].updates == {
        ("signal_type", "signal_value"): {"id": 1, "data": "test_data"}
    }
