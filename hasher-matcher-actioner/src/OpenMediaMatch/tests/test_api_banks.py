# Copyright (c) Meta Platforms, Inc. and affiliates.

from datetime import datetime, timedelta

from flask.testing import FlaskClient
from flask import Flask

from threatexchange.signal_type.pdq.signal import PdqSignal

from OpenMediaMatch.tests.utils import (
    app,
    client,
    create_bank,
    add_hash_to_bank,
    IMAGE_URL_TO_PDQ,
)
from OpenMediaMatch.background_tasks.build_index import build_all_indices
from OpenMediaMatch.persistence import get_storage


def test_banks_empty_index(client: FlaskClient):
    response = client.get("/c/banks")
    assert response.status_code == 200
    assert response.json == []


def test_banks_create(client: FlaskClient):
    # Must not start with number
    post_response = client.post(
        "/c/banks",
        json={"name": "01_TEST_BANK"},
    )
    assert post_response.status_code == 400

    # Cannot contain lowercase letters
    post_response = client.post(
        "/c/banks",
        json={"name": "my_test_bank"},
    )
    assert post_response.status_code == 400

    post_response = client.post(
        "/c/banks",
        json={"name": "MY_TEST_BANK_01"},
    )
    assert post_response.status_code == 201
    assert post_response.json == {
        "matching_enabled_ratio": 1.0,
        "name": "MY_TEST_BANK_01",
    }

    # Should now be visible on index
    response = client.get("/c/banks")
    assert response.status_code == 200
    assert response.json == [post_response.json]


def test_banks_update(client: FlaskClient):
    post_response = client.post(
        "/c/banks",
        json={"name": "MY_TEST_BANK"},
    )
    assert post_response.status_code == 201

    # check name validation
    post_response = client.put(
        "/c/bank/MY_TEST_BANK",
        json={"name": "1_invalid_name"},
    )
    assert post_response.status_code == 400

    # check update with rename
    post_response = client.put(
        "/c/bank/MY_TEST_BANK",
        json={"name": "MY_TEST_BANK_RENAMED"},
    )
    assert post_response.status_code == 200
    assert post_response.get_json()["name"] == "MY_TEST_BANK_RENAMED"

    # check update without rename
    post_response = client.put(
        "/c/bank/MY_TEST_BANK_RENAMED",
        json={"enabled": False},
    )
    assert post_response.status_code == 200
    assert post_response.get_json()["matching_enabled_ratio"] == 0

    # check update without ratio
    post_response = client.put(
        "/c/bank/MY_TEST_BANK_RENAMED",
        json={"enabled_ratio": 0.5},
    )
    assert post_response.status_code == 200
    assert post_response.get_json()["matching_enabled_ratio"] == 0.5

    # Final test to make sure we only have one bank with proper name and disabled

    get_response = client.get("/c/banks")
    assert get_response.status_code == 200
    json = get_response.get_json()
    assert len(json) == 1
    assert json[0] == {"name": "MY_TEST_BANK_RENAMED", "matching_enabled_ratio": 0.5}


def test_banks_delete(client: FlaskClient):
    post_response = client.post(
        "/c/banks",
        json={"name": "MY_TEST_BANK"},
    )
    assert post_response.status_code == 201

    # check name validation
    post_response = client.delete(
        "/c/bank/MY_TEST_BANK",
    )
    assert post_response.status_code == 200

    # deleting non existing bank should succeed
    post_response = client.delete(
        "/c/bank/MY_TEST_BANK",
    )
    assert post_response.status_code == 200


def test_bank_get_content(client: FlaskClient):
    bank_name = "TEST_BANK_GET"
    create_bank(client, bank_name)

    # Add content
    image_url = "https://github.com/facebook/ThreatExchange/blob/main/pdq/data/bridge-mods/aaa-orig.jpg?raw=true"
    add_response = client.post(
        f"/c/bank/{bank_name}/content?url={image_url}&content_type=photo"
    )
    assert add_response.status_code == 200, str(add_response.get_json())
    assert add_response.json
    content_id = add_response.json.get("id")

    # Get content by id
    get_response = client.get(f"/c/bank/{bank_name}/content/{content_id}")
    assert get_response.status_code == 200, str(get_response.get_json())
    assert get_response.json
    assert get_response.json.get("id") == content_id


def test_bank_get_content_404(client: FlaskClient):
    bank_name = "TEST_BANK_GET"
    content_id = 1

    # Bank does not exist
    get_response = client.get(f"/c/bank/{bank_name}/content/{content_id}")
    assert get_response.status_code == 404, str(get_response.get_json())

    create_bank(client, bank_name)

    # Content does not exist
    get_response = client.get(f"/c/bank/{bank_name}/content/{content_id}")
    assert get_response.status_code == 404, str(get_response.get_json())


def test_banks_add_content(client: FlaskClient):
    bank_name = "NEW_BANK"
    create_bank(client, bank_name)

    image_url = "https://github.com/facebook/ThreatExchange/blob/main/pdq/data/bridge-mods/aaa-orig.jpg?raw=true"

    post_response = client.post(
        f"/c/bank/{bank_name}/content?url={image_url}&content_type=photo"
    )

    assert post_response.status_code == 200, str(post_response.get_json())
    assert post_response.json == {
        "id": 1,
        "signals": {
            "pdq": "f8f8f0cee0f4a84f06370a22038f63f0b36e2ed596621e1d33e6b39c4e9c9b22"
        },
    }


def test_bank_update_content(client: FlaskClient):
    bank_name = "TEST_BANK_UPDATE"
    create_bank(client, bank_name)

    # Add content
    image_url = "https://github.com/facebook/ThreatExchange/blob/main/pdq/data/bridge-mods/aaa-orig.jpg?raw=true"
    add_response = client.post(
        f"/c/bank/{bank_name}/content?url={image_url}&content_type=photo"
    )
    assert add_response.status_code == 200, str(add_response.get_json())
    assert add_response.json
    content_id = add_response.json.get("id")

    # Define new disable_until_ts value and update content
    new_disable_ts = int((datetime.now() + timedelta(days=365)).timestamp())
    update_response = client.put(
        f"/c/bank/{bank_name}/content/{content_id}",
        json={"disable_until_ts": new_disable_ts},
    )
    assert update_response.status_code == 200, str(update_response.get_json())
    assert update_response.json
    updated_content = update_response.json
    assert updated_content.get("disable_until_ts") == new_disable_ts


def test_bank_update_content_400(client: FlaskClient):
    bank_name = "TEST_BANK_UPDATE"
    create_bank(client, bank_name)

    # Add content
    image_url = "https://github.com/facebook/ThreatExchange/blob/main/pdq/data/bridge-mods/aaa-orig.jpg?raw=true"
    add_response = client.post(
        f"/c/bank/{bank_name}/content?url={image_url}&content_type=photo"
    )
    assert add_response.status_code == 200, str(add_response.get_json())
    assert add_response.json
    content_id = add_response.json.get("id")

    # Define new disable_until_ts value too far in the future and update content
    new_disable_ts = 9999999999
    update_response = client.put(
        f"/c/bank/{bank_name}/content/{content_id}",
        json={"disable_until_ts": new_disable_ts},
    )
    assert update_response.status_code == 400, str(update_response.get_json())


def test_banks_delete_content(client: FlaskClient):
    bank_name = "NEW_BANK"
    image_url = "https://github.com/facebook/ThreatExchange/blob/main/pdq/data/bridge-mods/aaa-orig.jpg?raw=true"

    create_bank(client, bank_name)
    add_hash_to_bank(client, bank_name, image_url, 1)

    post_response = client.delete(f"/c/bank/{bank_name}/content/1")

    assert post_response.status_code == 200
    assert post_response.json == {"deleted": 1}


def test_banks_add_metadata(client: FlaskClient):
    bank_name = "NEW_BANK"
    create_bank(client, bank_name)

    image_url = "https://github.com/facebook/ThreatExchange/blob/main/pdq/data/bridge-mods/aaa-orig.jpg?raw=true"
    post_request = f"/c/bank/{bank_name}/content?url={image_url}&content_type=photo"

    post_response = client.post(
        post_request, json={"metadata": {"invalid_metadata": 5}}
    )
    assert post_response.status_code == 400, str(post_response.get_json())

    post_response = client.post(
        post_request,
        json={"metadata": {"content_id": "1197433091", "json": {"asdf": {}}}},
    )

    assert post_response.status_code == 200, str(post_response.get_json())


def test_banks_add_hash_index(app: Flask, client: FlaskClient):
    bank_name = "NEW_BANK"
    bank_name_2 = "NEW_BANK_2"
    image_url = "https://github.com/facebook/ThreatExchange/blob/main/pdq/data/bridge-mods/aaa-orig.jpg?raw=true"
    image_url_2 = "https://github.com/facebook/ThreatExchange/blob/main/pdq/data/misc-images/c.png?raw=true"

    # Make two banks and add images to each bank
    create_bank(client, bank_name)
    add_hash_to_bank(client, bank_name, image_url, 1)
    create_bank(client, bank_name_2)
    add_hash_to_bank(client, bank_name, image_url_2, 2)

    storage = get_storage()
    # ensure index is empty to start with
    assert storage.get_signal_type_index(PdqSignal) is None

    # Build index
    build_all_indices(storage, storage, storage)

    # Test against first image
    post_response = client.get(
        f"/m/raw_lookup?signal_type=pdq&signal={IMAGE_URL_TO_PDQ[image_url]}"
    )
    assert post_response.status_code == 200
    assert post_response.json == {"matches": [1]}

    # Test against second image
    post_response = client.get(
        f"/m/raw_lookup?signal_type=pdq&signal={IMAGE_URL_TO_PDQ[image_url_2]}"
    )
    assert post_response.status_code == 200
    assert post_response.json == {"matches": [2]}


def test_bank_get_content_signal_validation(client: FlaskClient):
    """Test signal type validation for bank content retrieval"""
    bank_name = "TEST_BANK"
    create_bank(client, bank_name)

    # Add some content with a PDQ signal
    response = client.post(
        f"/c/bank/{bank_name}/signal",
        json={"pdq": "0" * 64},
    )
    assert response.status_code == 200
    content_id = response.json["id"]

    # Test valid signal type without signals
    response = client.get(
        f"/c/bank/{bank_name}/content/{content_id}?signal_type=video_md5"
    )
    assert response.status_code == 200
    assert isinstance(response.json, dict)
    assert "signals" in response.json
    assert response.json["signals"] == {}

    # Test a valid signal type with signals
    response = client.get(f"/c/bank/{bank_name}/content/{content_id}?signal_type=pdq")
    assert response.status_code == 200
    assert isinstance(response.json, dict)
    assert "signals" in response.json
    assert response.json["signals"] == {"pdq": "0" * 64}

    # Test an invalid signal type
    response = client.get(
        f"/c/bank/{bank_name}/content/{content_id}?signal_type=invalid"
    )
    assert response.status_code == 400
    assert isinstance(response.json, dict)
    assert "message" in response.json
    assert "No such signal type" in response.json["message"]
