# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Tests for credentials scoped to a single exchange (and its bank).
"""

from dataclasses import dataclass
import json
import logging
import pathlib
import threading
import typing as t

import flask_migrate
import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import inspect, select, text

import OpenMediaMatch
from OpenMediaMatch.background_tasks import fetcher
from OpenMediaMatch.persistence import get_storage
from OpenMediaMatch.storage.postgres import database, impl
from OpenMediaMatch.storage.postgres.impl import DefaultOMMStore
from OpenMediaMatch.tests.utils import app, client

from threatexchange.exchanges import auth
from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.exchanges.fetch_state import TFetchCheckpoint
from threatexchange.exchanges.impl.static_sample import StaticSampleSignalExchangeAPI
from threatexchange.exchanges.signal_exchange_api import TSignalExchangeAPICls
from threatexchange.signal_type.signal_base import SignalType

FAKE_API = "fake_auth"
ENV_VARIABLE = "OMM_TEST_FAKE_EXCHANGE_CREDENTIALS"

TOKEN_A = "fake-token-exchange-a"
TOKEN_B = "fake-token-exchange-b"
TOKEN_API = "fake-token-api-level"
TOKEN_ENV = "fake-token-environment"


@dataclass
class _FakeCredentials(auth.CredentialHelper):
    ENV_VARIABLE: t.ClassVar[str] = ENV_VARIABLE

    token: str
    region: t.Optional[str] = None

    @classmethod
    def _from_str(cls, s: str) -> "_FakeCredentials":
        return cls(s.strip())

    def _are_valid(self) -> bool:
        return bool(self.token)


class _FakeAuthExchangeAPI(
    auth.SignalExchangeWithAuth[CollaborationConfigBase, _FakeCredentials],
    StaticSampleSignalExchangeAPI,
):
    """Sample data, but requires credentials and records which were used."""

    # Tests can set this to pause every for_collab() until N callers arrive
    for_collab_barrier: t.ClassVar[t.Optional[threading.Barrier]] = None
    # collab name -> token used by fetch_iter()
    fetched_with: t.ClassVar[t.Dict[str, str]] = {}

    def __init__(
        self, collab: CollaborationConfigBase, credentials: _FakeCredentials
    ) -> None:
        self.collab = collab
        self.credentials = credentials

    @classmethod
    def get_name(cls) -> str:
        return FAKE_API

    @staticmethod
    def get_credential_cls() -> t.Type[_FakeCredentials]:
        return _FakeCredentials

    @classmethod
    def for_collab(
        cls,
        collab: CollaborationConfigBase,
        credentials: t.Optional[_FakeCredentials] = None,
    ) -> "_FakeAuthExchangeAPI":
        if cls.for_collab_barrier is not None:
            cls.for_collab_barrier.wait()
        credentials = credentials or _FakeCredentials.get(cls)
        return cls(collab, credentials)

    def fetch_iter(
        self,
        supported_signal_types: t.Sequence[t.Type[SignalType]],
        checkpoint: t.Optional[TFetchCheckpoint],
    ):
        type(self).fetched_with[self.collab.name] = self.credentials.token
        yield from super().fetch_iter(supported_signal_types, checkpoint)


@pytest.fixture(autouse=True)
def _enable_ui(monkeypatch: pytest.MonkeyPatch) -> None:
    # Autouse, so it runs before the app fixture reads config
    monkeypatch.setenv("OMM_UI_ENABLED", "true")


@pytest.fixture()
def storage(app: Flask, monkeypatch: pytest.MonkeyPatch) -> t.Iterator[DefaultOMMStore]:
    monkeypatch.delenv(ENV_VARIABLE, raising=False)
    storage_instance = get_storage()
    assert isinstance(storage_instance, DefaultOMMStore)
    storage_instance.exchange_types = {
        api_cls.get_name(): api_cls
        for api_cls in t.cast(
            t.List[TSignalExchangeAPICls],
            [StaticSampleSignalExchangeAPI, _FakeAuthExchangeAPI],
        )
    }
    _FakeAuthExchangeAPI.fetched_with = {}
    _FakeAuthExchangeAPI.for_collab_barrier = None
    yield storage_instance
    _FakeAuthExchangeAPI.for_collab_barrier = None
    assert _FakeCredentials._DEFAULT is None, "process-global credentials leaked"


def _create_exchange(
    client: FlaskClient,
    name: str,
    credential_json: t.Any = None,
    api: str = FAKE_API,
    expected_status: int = 201,
):
    body: t.Dict[str, t.Any] = {"api": api, "bank": name, "api_json": {}}
    if credential_json is not None:
        body["credential_json"] = credential_json
    resp = client.post("/c/exchanges", json=body)
    assert resp.status_code == expected_status, resp.get_json()
    return resp


def _set_exchange_creds(client: FlaskClient, name: str, credential_json: t.Any):
    return client.post(
        f"/c/exchange/{name}/credentials", json={"credential_json": credential_json}
    )


def _set_api_creds(client: FlaskClient, credential_json: t.Any):
    resp = client.post(
        f"/c/exchanges/api/{FAKE_API}", json={"credential_json": credential_json}
    )
    assert resp.status_code == 200, resp.get_json()


def _client_token(storage: DefaultOMMStore, name: str) -> str:
    collab = storage.exchange_get(name)
    assert collab is not None
    api_client = storage.exchange_get_client(collab)
    assert isinstance(api_client, _FakeAuthExchangeAPI)
    return api_client.credentials.token


def _source(client: FlaskClient, name: str) -> t.Optional[str]:
    resp = client.get(f"/c/exchange/{name}/credentials")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data is not None
    return data["source"]


def _stored_credentials_json(name: str) -> t.Any:
    return database.db.session.execute(
        select(database.ExchangeConfig.credentials_json).where(
            database.ExchangeConfig.name == name
        )
    ).scalar_one_or_none()


def test_same_api_exchanges_use_own_credentials(
    storage: DefaultOMMStore, client: FlaskClient
) -> None:
    _set_api_creds(client, {"token": TOKEN_API})
    _create_exchange(client, "EX_A", {"token": TOKEN_A})
    _create_exchange(client, "EX_B", {"token": TOKEN_B})
    _create_exchange(client, "EX_C")  # No credentials of its own

    # Built in sequence, in both orders
    assert _client_token(storage, "EX_A") == TOKEN_A
    assert _client_token(storage, "EX_B") == TOKEN_B
    assert _client_token(storage, "EX_C") == TOKEN_API
    assert _client_token(storage, "EX_B") == TOKEN_B
    assert _client_token(storage, "EX_A") == TOKEN_A

    fetcher.fetch_all(storage, storage.get_signal_type_configs())
    assert _FakeAuthExchangeAPI.fetched_with == {
        "EX_A": TOKEN_A,
        "EX_B": TOKEN_B,
        "EX_C": TOKEN_API,
    }
    for name in ("EX_A", "EX_B", "EX_C"):
        status = storage.exchange_get_fetch_status(name)
        assert status.last_fetch_succeeded is True
        assert status.fetched_items > 0


def test_concurrent_client_construction_is_isolated(
    app: Flask, storage: DefaultOMMStore, client: FlaskClient
) -> None:
    _create_exchange(client, "EX_A", {"token": TOKEN_A})
    _create_exchange(client, "EX_B", {"token": TOKEN_B})

    # Both threads are inside for_collab() at the same time before either
    # resolves credentials. With a process-global default, one of them
    # would see the other's credentials (or none).
    _FakeAuthExchangeAPI.for_collab_barrier = threading.Barrier(2, timeout=10)
    results: t.Dict[str, str] = {}
    errors: t.List[BaseException] = []

    def build(name: str) -> None:
        try:
            with app.app_context():
                results[name] = _client_token(storage, name)
        except BaseException as e:
            errors.append(e)

    threads = [threading.Thread(target=build, args=(n,)) for n in ("EX_A", "EX_B")]
    for th in threads:
        th.start()
    for th in threads:
        th.join(timeout=30)

    assert not errors
    assert results == {"EX_A": TOKEN_A, "EX_B": TOKEN_B}


def test_credential_fallback_order(
    storage: DefaultOMMStore, client: FlaskClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _create_exchange(client, "EX_A")

    # Nothing anywhere
    assert _source(client, "EX_A") is None
    collab = storage.exchange_get("EX_A")
    assert collab is not None
    with pytest.raises(auth.SignalExchangeAPIMissingAuthException):
        storage.exchange_get_client(collab)

    # Populated but invalid environment isn't reported as usable
    monkeypatch.setenv(ENV_VARIABLE, "   ")
    assert _source(client, "EX_A") is None

    # Environment
    monkeypatch.setenv(ENV_VARIABLE, TOKEN_ENV)
    assert _source(client, "EX_A") == "environment"
    assert _client_token(storage, "EX_A") == TOKEN_ENV

    # API-level beats environment
    _set_api_creds(client, {"token": TOKEN_API})
    assert _source(client, "EX_A") == "api"
    assert _client_token(storage, "EX_A") == TOKEN_API

    # Exchange beats API-level
    assert _set_exchange_creds(client, "EX_A", {"token": TOKEN_A}).status_code == 200
    assert _source(client, "EX_A") == "exchange"
    assert _client_token(storage, "EX_A") == TOKEN_A

    # Unwind
    assert _set_exchange_creds(client, "EX_A", {}).status_code == 200
    assert _client_token(storage, "EX_A") == TOKEN_API
    _set_api_creds(client, {})
    assert _client_token(storage, "EX_A") == TOKEN_ENV


def test_create_update_clear_delete(
    storage: DefaultOMMStore, client: FlaskClient
) -> None:
    _create_exchange(client, "EX_A", {"token": TOKEN_A, "region": "test-region"})
    assert _stored_credentials_json("EX_A") == {
        "token": TOKEN_A,
        "region": "test-region",
    }
    resp = client.get("/c/exchange/EX_A")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data is not None
    assert data["name"] == "EX_A"
    assert data["credential_status"] == {
        "supports_auth": True,
        "has_credentials": True,
        "source": "exchange",
    }

    # Update
    resp = _set_exchange_creds(client, "EX_A", {"token": TOKEN_B})
    assert resp.status_code == 200
    assert resp.get_json() == {
        "supports_auth": True,
        "has_credentials": True,
        "source": "exchange",
    }
    assert _client_token(storage, "EX_A") == TOKEN_B

    # Clear with null
    resp = _set_exchange_creds(client, "EX_A", None)
    assert resp.status_code == 200
    assert resp.get_json() == {
        "supports_auth": True,
        "has_credentials": False,
        "source": None,
    }
    assert _stored_credentials_json("EX_A") is None
    assert storage.exchange_get_credentials("EX_A") is None

    # Delete removes them along with the exchange
    assert _set_exchange_creds(client, "EX_A", {"token": TOKEN_A}).status_code == 200
    assert client.delete("/c/exchange/EX_A").status_code == 200
    assert (
        database.db.session.execute(
            text("SELECT count(1) FROM exchange WHERE name = 'EX_A'")
        ).scalar_one()
        == 0
    )
    assert storage.exchange_get_credentials("EX_A") is None
    _create_exchange(client, "EX_A")
    assert _stored_credentials_json("EX_A") is None
    assert _source(client, "EX_A") is None

    # Unknown exchange
    assert client.get("/c/exchange/NO_SUCH/credentials").status_code == 404
    assert _set_exchange_creds(client, "NO_SUCH", {"token": TOKEN_A}).status_code == 404


def test_invalid_credentials_rejected_without_echo(
    storage: DefaultOMMStore, client: FlaskClient
) -> None:
    secret = "fake-secret-must-not-echo"
    bad_payloads: t.List[t.Any] = [
        {"token": secret, "unexpected": secret},  # Extra field
        {secret: secret},  # Unknown field, secret as key
        {"region": secret},  # Missing required field
        {"token": [secret]},  # Not a scalar
        {"token": 12345, "region": secret},  # Wrong type
        {"token": "", "region": secret},  # Fails _are_valid()
        {"token": secret + "\x00"},
        {"token": secret * 1000},  # Too long
        secret,  # Not an object
    ]
    for payload in bad_payloads:
        resp = _create_exchange(client, "EX_BAD", payload, expected_status=400)
        assert secret not in resp.get_data(as_text=True)
        # Nothing was created
        assert client.get("/c/exchange/EX_BAD").status_code == 404

    _create_exchange(client, "EX_A")
    for payload in bad_payloads:
        resp = _set_exchange_creds(client, "EX_A", payload)
        assert resp.status_code == 400
        assert secret not in resp.get_data(as_text=True)
    assert _stored_credentials_json("EX_A") is None

    # Only credential_json is accepted by the per-exchange endpoint
    resp = client.post(
        "/c/exchange/EX_A/credentials",
        json={"credential_json": {"token": TOKEN_A}, "other": secret},
    )
    assert resp.status_code == 400
    assert client.post("/c/exchange/EX_A/credentials", json={}).status_code == 400

    # API-level endpoint also rejects unknown fields
    resp = client.post(
        f"/c/exchanges/api/{FAKE_API}",
        json={"credential_json": {"token": TOKEN_API, "unexpected": secret}},
    )
    assert resp.status_code == 400
    assert secret not in resp.get_data(as_text=True)

    # APIs that don't use credentials reject them
    resp = _create_exchange(
        client, "EX_SAMPLE", {"token": secret}, api="sample", expected_status=400
    )
    assert secret not in resp.get_data(as_text=True)
    _create_exchange(client, "EX_SAMPLE", api="sample")
    resp = _set_exchange_creds(client, "EX_SAMPLE", {"token": secret})
    assert resp.status_code == 400
    assert client.get("/c/exchange/EX_SAMPLE/credentials").get_json() == {
        "supports_auth": False,
        "has_credentials": False,
        "source": None,
    }


def test_storage_without_exchange_credentials(
    storage: DefaultOMMStore, client: FlaskClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(storage, "exchange_credentials_supported", lambda: False)
    _create_exchange(client, "EX_A", {"token": TOKEN_A}, expected_status=501)
    # Rejected before anything was created
    assert client.get("/c/exchange/EX_A").status_code == 404

    _create_exchange(client, "EX_A")
    assert _set_exchange_creds(client, "EX_A", {"token": TOKEN_A}).status_code == 501
    assert _stored_credentials_json("EX_A") is None


def test_create_cleans_up_when_storing_credentials_fails(
    storage: DefaultOMMStore, client: FlaskClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(*args: t.Any) -> None:
        raise RuntimeError("simulated storage failure")

    monkeypatch.setattr(impl, "_check_credentials_for_api", fail)
    resp = _create_exchange(client, "EX_A", {"token": TOKEN_A}, expected_status=500)
    assert TOKEN_A not in resp.get_data(as_text=True)
    assert client.get("/c/exchange/EX_A").status_code == 404
    assert storage.get_bank("EX_A") is None


def test_credential_values_never_returned_or_logged(
    storage: DefaultOMMStore, client: FlaskClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    # As if SQLALCHEMY_ENGINE_LOG_LEVEL = logging.INFO
    caplog.set_level(logging.INFO, logger="sqlalchemy.engine")
    _set_api_creds(client, {"token": TOKEN_API})
    _create_exchange(client, "EX_A", {"token": TOKEN_A})
    _create_exchange(client, "EX_B")
    assert _set_exchange_creds(client, "EX_B", {"token": TOKEN_B}).status_code == 200
    fetcher.fetch_all(storage, storage.get_signal_type_configs())

    for url in (
        "/c/exchanges",
        "/c/exchange/EX_A",
        "/c/exchange/EX_B",
        "/c/exchange/EX_A/credentials",
        "/c/exchange/EX_B/credentials",
        "/c/exchange/EX_A/status",
        f"/c/exchanges/api/{FAKE_API}",
        "/ui/",
        "/ui/exchanges",
    ):
        resp = client.get(url)
        assert resp.status_code == 200, url
        body = resp.get_data(as_text=True)
        for token in (TOKEN_A, TOKEN_B, TOKEN_API):
            assert token not in body, url

    assert "INSERT INTO" in caplog.text, "SQL logging should have been captured"
    for token in (TOKEN_A, TOKEN_B, TOKEN_API):
        assert token not in caplog.text


def test_migration_upgrade_downgrade(app: Flask) -> None:
    migrations_dir = str(pathlib.Path(OpenMediaMatch.__file__).parent / "migrations")
    this_revision = "b7e4c2a9d1f0"
    previous_revision = "53fb7741007a"
    sesh = database.db.session

    shared_creds = {"token": "fake-token-shared-api-level"}
    orphan_creds = {"token": "fake-token-no-exchanges"}
    rotated_creds = {"token": "fake-token-rotated"}

    def exchange_columns() -> t.Set[str]:
        sesh.commit()
        return {c["name"] for c in inspect(database.db.engine).get_columns("exchange")}

    def api_level() -> t.Dict[str, t.Any]:
        rows = sesh.execute(
            text("SELECT api, default_credentials_json FROM exchange_api_config")
        ).all()
        sesh.commit()  # Release the read lock, or ALTER TABLE waits forever
        return dict(rows)

    def exchange_creds() -> t.Dict[str, t.Any]:
        rows = sesh.execute(text("SELECT name, credentials_json FROM exchange")).all()
        sesh.commit()
        return dict(rows)

    database.db.drop_all()
    sesh.execute(text("DROP TABLE IF EXISTS alembic_version"))
    sesh.commit()
    try:
        # An existing deployment, before this change: credentials only at the
        # API level, shared by every exchange of that API
        flask_migrate.upgrade(directory=migrations_dir, revision=previous_revision)
        assert "credentials_json" not in exchange_columns()
        for i, (name, api) in enumerate(
            [
                ("OLD_FAKE_1", FAKE_API),
                ("OLD_FAKE_2", FAKE_API),
                ("OLD_SAMPLE", "sample"),
            ],
            start=1,
        ):
            sesh.execute(
                text(
                    "INSERT INTO exchange (id, name, api_cls, retain_api_data, "
                    "fetching_enabled, retain_data_with_unknown_signal_types, "
                    "typed_config) VALUES (:id, :name, :api, false, true, false, '{}')"
                ),
                {"id": i, "name": name, "api": api},
            )
        for api, creds in [
            (FAKE_API, shared_creds),
            ("api_without_exchanges", orphan_creds),
            ("sample", {}),
        ]:
            sesh.execute(
                text(
                    "INSERT INTO exchange_api_config (api, default_credentials_json) "
                    "VALUES (:api, CAST(:creds AS JSON))"
                ),
                {"api": api, "creds": json.dumps(creds)},
            )
        sesh.commit()

        # Upgrade moves API-level credentials onto the exchanges using them
        flask_migrate.upgrade(directory=migrations_dir, revision=this_revision)
        assert "credentials_json" in exchange_columns()
        assert exchange_creds() == {
            "OLD_FAKE_1": shared_creds,
            "OLD_FAKE_2": shared_creds,
            "OLD_SAMPLE": None,
        }
        assert api_level() == {
            FAKE_API: {},
            "api_without_exchanges": orphan_creds,  # Nobody to own them
            "sample": {},
        }

        # One exchange rotates, then downgrade restores one API-level set
        sesh.execute(
            text(
                "UPDATE exchange SET credentials_json = CAST(:creds AS JSON) "
                "WHERE name = 'OLD_FAKE_2'"
            ),
            {"creds": json.dumps(rotated_creds)},
        )
        sesh.commit()
        flask_migrate.downgrade(directory=migrations_dir, revision=previous_revision)
        assert "credentials_json" not in exchange_columns()
        assert api_level() == {
            FAKE_API: shared_creds,  # From the oldest exchange
            "api_without_exchanges": orphan_creds,
            "sample": {},
        }
        names: t.Sequence[str] = (
            sesh.execute(text("SELECT name FROM exchange")).scalars().all()
        )
        sesh.commit()
        assert set(names) == {"OLD_FAKE_1", "OLD_FAKE_2", "OLD_SAMPLE"}

        flask_migrate.upgrade(directory=migrations_dir, revision=this_revision)
        assert "credentials_json" in exchange_columns()
        assert exchange_creds()["OLD_FAKE_2"] == shared_creds
    finally:
        sesh.rollback()
        database.db.drop_all()
        sesh.execute(text("DROP TABLE IF EXISTS alembic_version"))
        sesh.commit()
        database.db.create_all()
