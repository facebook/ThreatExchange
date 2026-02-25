# Copyright (c) Meta Platforms, Inc. and affiliates.

from io import BytesIO
import tempfile
import typing as t
import time

from pytest import MonkeyPatch
from flask.testing import FlaskClient
from flask import Flask
from PIL import Image
import requests

from threatexchange.exchanges.impl.fb_threatexchange_api import (
    FBThreatExchangeSignalExchangeAPI,
    FBThreatExchangeCredentials,
)
from threatexchange.utils import dataclass_json
from threatexchange.exchanges.impl.static_sample import StaticSampleSignalExchangeAPI
from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.pdq.pdq_index2 import PDQIndex2

from OpenMediaMatch.tests.utils import app, client, create_bank
from OpenMediaMatch.background_tasks.build_index import build_all_indices
from OpenMediaMatch.persistence import get_storage
from OpenMediaMatch.blueprints import matching
from OpenMediaMatch.storage import interface


def test_status_response(client: FlaskClient, monkeypatch: MonkeyPatch):
    response = client.get("/status")
    assert response.status_code == 200
    assert response.data == b"I-AM-ALIVE"

    cache_val = matching._SignalIndexInMemoryCache(
        PdqSignal,
        PDQIndex2(),
        interface.SignalTypeIndexBuildCheckpoint(0, 0, 0),
        last_check_ts=0.0,
        sec_old_before_stale=0,
    )

    def fake_cache() -> matching.IndexCache:
        return {PdqSignal.get_name(): cache_val}

    # We can't easily run the caching tasks in tests,
    # but we can fake it
    monkeypatch.setattr(matching, "_get_index_cache", fake_cache)

    assert not cache_val.is_ready
    response = client.get("/status")
    assert response.status_code == 503
    assert response.data == b"INDEX-NOT-LOADED"

    # We also are okay if the cache is old but we configured to not care
    cache_val.last_check_ts = 1

    response = client.get("/status")
    assert response.status_code == 200
    assert response.data == b"I-AM-ALIVE"

    # But if we do care, status should be no good
    cache_val.sec_old_before_stale = 65

    response = client.get("/status")
    assert response.status_code == 503
    assert response.data == b"INDEX-STALE"

    cache_val.last_check_ts = time.time()
    response = client.get("/status")
    assert response.status_code == 200
    assert response.data == b"I-AM-ALIVE"


def test_openapi_documentation_available(client: FlaskClient):
    response = client.get("/openapi/openapi.json")
    assert response.status_code == 200
    assert response.is_json
    payload = response.get_json()
    assert payload is not None
    assert payload.get("info", {}).get("title") == "Open Media Match API"


def test_lookup_success(app: Flask, client: FlaskClient):
    storage = get_storage()
    # ensure index is empty to start with
    assert storage.get_signal_type_index(PdqSignal) is None

    # Build index
    build_all_indices(storage, storage, storage)

    # test GET
    image_url = "https://github.com/facebook/ThreatExchange/blob/main/pdq/data/bridge-mods/aaa-orig.jpg?raw=true"
    get_resp = client.get(f"/m/lookup?url={image_url}")
    assert get_resp.status_code == 200

    # test POST with temp file
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))
    with tempfile.NamedTemporaryFile(suffix=".jpg") as f:
        image.save(f, format="JPEG")
        file_tuple = (f.name, f.name, "image/jpeg")
        resp = client.post("/m/lookup", data={"photo": file_tuple})
        assert resp.status_code == 200

        # It's not really a video, but MD5 is simple that we can fake it
        resp = client.post("/m/lookup", data={"video": file_tuple})
        assert resp.status_code == 200


def test_lookup_without_role(app: Flask, client: FlaskClient):
    # role resets to True in the next test
    client.application.config["ROLE_HASHER"] = False

    # test GET
    image_url = "https://github.com/facebook/ThreatExchange/blob/main/pdq/data/bridge-mods/aaa-orig.jpg?raw=true"
    get_resp = client.get(f"/m/lookup?url={image_url}")
    assert get_resp.status_code == 403

    # test POST with temp file
    with tempfile.NamedTemporaryFile(suffix=".jpg") as f:
        # Write a minimal valid JPEG file header
        f.write(
            b"\xff\xd8\xff\xe0\x00\x10\x4a\x46\x49\x46\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9"
        )
        f.flush()
        files = {"file": (f.name, f.name, "image/jpeg")}
        resp = client.post("/m/lookup", data=files)
        assert resp.status_code == 403


def test_exchange_api_set_auth(app: Flask, client: FlaskClient):
    storage = get_storage()
    sample_name = StaticSampleSignalExchangeAPI.get_name()
    tx_name = FBThreatExchangeSignalExchangeAPI.get_name()
    # Monkeypatch installed types
    storage.exchange_types = {  # type: ignore
        api_cls.get_name(): api_cls
        for api_cls in (
            FBThreatExchangeSignalExchangeAPI,
            StaticSampleSignalExchangeAPI,
        )
    }
    resp = client.get("/c/exchanges/apis")
    assert resp.status_code == 200
    assert set(t.cast(list, resp.json)) == {sample_name, tx_name}

    resp = client.get(f"/c/exchanges/api/{sample_name}")
    assert resp.status_code == 200
    assert resp.json == {
        "supports_authentification": False,
        "has_set_authentification": False,
    }

    resp = client.get(f"/c/exchanges/api/{tx_name}")
    assert resp.status_code == 200
    assert resp.json == {
        "supports_authentification": True,
        "has_set_authentification": False,
    }

    creds = FBThreatExchangeCredentials("12345789|000000000000")

    resp = client.post(
        f"/c/exchanges/api/{tx_name}",
        json={"credential_json": dataclass_json.dataclass_dump_dict(creds)},
    )

    assert resp.status_code == 200
    assert resp.json == {
        "supports_authentification": True,
        "has_set_authentification": True,
    }

    resp = client.get(f"/c/exchanges/api/{tx_name}")
    assert resp.status_code == 200
    assert resp.json == {
        "supports_authentification": True,
        "has_set_authentification": True,
    }

    # Unset
    resp = client.post(
        f"/c/exchanges/api/{tx_name}",
        json={"credential_json": {}},
    )
    assert resp.status_code == 200
    assert resp.json == {
        "supports_authentification": True,
        "has_set_authentification": False,
    }


def test_exchange_api_schema(app: Flask, client: FlaskClient):
    """Schema endpoint returns config and optional credential field descriptors."""
    storage = get_storage()
    sample_name = StaticSampleSignalExchangeAPI.get_name()
    tx_name = FBThreatExchangeSignalExchangeAPI.get_name()
    # Patch installed types so both sample and fb_threatexchange are available
    storage.exchange_types = {  # type: ignore[attr-defined]
        api_cls.get_name(): api_cls
        for api_cls in (
            StaticSampleSignalExchangeAPI,
            FBThreatExchangeSignalExchangeAPI,
        )
    }

    # Sample API has no type-specific config fields and no credentials
    resp = client.get(f"/c/exchanges/api/{sample_name}/schema")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data is not None and isinstance(data, dict)
    assert "config_schema" in data
    assert "fields" in data["config_schema"]
    assert data["credentials_schema"] is None

    # FB ThreatExchange has config (e.g. privacy_group) and credentials (api_token)
    resp = client.get(f"/c/exchanges/api/{tx_name}/schema")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data is not None and isinstance(data, dict)
    assert "config_schema" in data
    config_fields = {f["name"]: f for f in data["config_schema"]["fields"]}
    assert "privacy_group" in config_fields
    assert config_fields["privacy_group"]["type"] == "number"
    assert config_fields["privacy_group"]["required"] is True
    cred_schema = data["credentials_schema"]
    assert cred_schema is not None
    cred_fields = {f["name"]: f for f in cred_schema["fields"]}
    assert "api_token" in cred_fields
    assert cred_fields["api_token"]["type"] == "string"


def test_compare_hashes(app: Flask, client: FlaskClient):
    specimen1 = "facd8bcb2a49bcebdec1985298d5fe84bcd006c187c598c720c3c087b3fdb318"
    specimen2 = "facd8bcb2a49bcebdec1985228d5ae84bcd006c187c598c720c2b087b3fdb318"
    # Happy path
    resp = client.post("/m/compare", json={"pdq": [specimen1, specimen2]})
    assert resp.json == {"pdq": [True, {"distance": 9}]}

    # Malformed input
    bad_inputs = [
        # Not a dict
        ["banana"],
        # Dict, but values are not lists
        {"pdq": "banana"},
        # List of comparison hashes is empty
        {"pdq": []},
        # Hashes are invalid
        {"pdq": ["banana", "banana"]},
        # Too many hashes (must be exactly 2)
        {"pdq": [specimen1, specimen2, specimen1]},
    ]
    for bad_input in bad_inputs:
        resp = client.post(
            "/m/compare",
            json=bad_input,
        )
        assert resp.status_code == 400


def test_exchange_delete(app: Flask, client: FlaskClient):
    delete_response = client.delete(
        "/c/exchange/TEST_EXCHANGE",
    )
    # deleting an exchange that doesn't exist returns 200
    assert delete_response.status_code == 200

    # create an exchange
    post_response = client.post(
        "/c/exchanges",
        json={"api": "sample", "bank": "FOO_EXCHANGE", "api_json": {}},
    )
    assert post_response.status_code == 201

    # test a real delete
    delete_response = client.delete(
        "/c/exchange/FOO_EXCHANGE",
    )
    assert delete_response.status_code == 200
    assert delete_response.get_json()["message"] == "Exchange deleted"


def test_exchange_get_fetch_status(app: Flask, client: FlaskClient):
    # Unknown exchange returns 404
    resp = client.get("/c/exchange/NONEXISTENT_EXCHANGE/status")
    assert resp.status_code == 404

    # Create an exchange and get fetch status
    post_resp = client.post(
        "/c/exchanges",
        json={"api": "sample", "bank": "BAR_EXCHANGE", "api_json": {}},
    )
    assert post_resp.status_code == 201

    resp = client.get("/c/exchange/BAR_EXCHANGE/status")
    assert resp.status_code == 200
    assert resp.is_json
    data = resp.get_json()
    assert data is not None
    # FetchStatus fields (from storage.interface.FetchStatus)
    assert "checkpoint_ts" in data
    assert "running_fetch_start_ts" in data
    assert "last_fetch_complete_ts" in data
    assert "last_fetch_succeeded" in data
    assert "up_to_date" in data
    assert "fetched_items" in data
