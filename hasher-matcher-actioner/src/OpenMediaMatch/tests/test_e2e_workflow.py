# Copyright (c) Meta Platforms, Inc. and affiliates.

from flask.testing import FlaskClient
from flask import Flask

from OpenMediaMatch.tests.utils import (
    app,
    client,
    create_bank,
)
from OpenMediaMatch.persistence import get_storage
from OpenMediaMatch.background_tasks.build_index import build_all_indices
from threatexchange.signal_type.pdq.signal import PdqSignal


def test_raw_hash_add_to_match_no_distance(app: Flask, client: FlaskClient):
    bank_name = "TEST_BANK"
    create_bank(client, bank_name)

    # PDQ hashes
    hashes = PdqSignal.get_examples()
    for pdq in hashes:
        resp = client.post(f"/c/bank/{bank_name}/signal", json={"pdq": pdq})
        assert resp.status_code == 200

    # No background tasks in the test, so let's trigger it manually
    storage = get_storage()
    build_all_indices(storage, storage, storage)

    # Sanity check that the index is build
    resp = client.get(f"/m/index/status?signal_type=pdq")
    assert resp.status_code == 200
    all_build_info = resp.json
    assert "pdq" in all_build_info  # type: ignore
    build_info = all_build_info["pdq"]  # type: ignore
    assert build_info["present"] == True
    assert build_info["size"] == len(hashes)

    # Now match
    resp = client.get(f"/m/raw_lookup?signal_type=pdq&signal={hashes[-1]}")
    assert resp.status_code == 200
    assert resp.json == {"matches": [16]}


def test_raw_hash_add_to_match_with_distance(app: Flask, client: FlaskClient):
    bank_name = "TEST_BANK"
    create_bank(client, bank_name)

    # PDQ hashes
    hashes = PdqSignal.get_examples()
    for pdq in hashes:
        resp = client.post(f"/c/bank/{bank_name}/signal", json={"pdq": pdq})
        assert resp.status_code == 200

    # No background tasks in the test, so let's trigger it manually
    storage = get_storage()
    build_all_indices(storage, storage, storage)

    # Sanity check that the index is build
    resp = client.get(f"/m/index/status?signal_type=pdq")
    assert resp.status_code == 200
    all_build_info = resp.json
    assert "pdq" in all_build_info  # type: ignore
    build_info = all_build_info["pdq"]  # type: ignore
    assert build_info["present"] == True
    assert build_info["size"] == len(hashes)

    # Now match
    resp = client.get(
        f"/m/raw_lookup?signal_type=pdq&include_distance=true&signal={hashes[-1]}"
    )
    assert resp.status_code == 200
    assert resp.json == {"matches": [{"content_id": 16, "distance": "0"}]}
