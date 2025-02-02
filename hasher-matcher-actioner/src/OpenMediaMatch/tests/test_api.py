# Copyright (c) Meta Platforms, Inc. and affiliates.

from io import BytesIO
import tempfile
import typing as t

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

from OpenMediaMatch.tests.utils import (
    app,
    client,
)
from OpenMediaMatch.background_tasks.build_index import build_all_indices
from OpenMediaMatch.persistence import get_storage


def test_status_response(client: FlaskClient):
    response = client.get("/status")
    assert response.status_code == 200
    assert response.data == b"I-AM-ALIVE"


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
        files = {"photo": (f.name, f.name, "image/jpeg")}
        resp = client.post("/m/lookup", data=files)
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
    storage.exchange_types = {
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
