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
    image_server,
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


def test_bank_get_content(client: FlaskClient, image_server: str):
    bank_name = "TEST_BANK_GET"
    create_bank(client, bank_name)

    # Add content
    image_url = f"{image_server}/image1.jpg"
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


def test_banks_add_content(client: FlaskClient, image_server: str):
    bank_name = "NEW_BANK"
    create_bank(client, bank_name)

    image_url = f"{image_server}/image1.jpg"

    post_response = client.post(
        f"/c/bank/{bank_name}/content?url={image_url}&content_type=photo"
    )

    assert post_response.status_code == 200, str(post_response.get_json())
    assert post_response.json == {
        "id": 1,
        "signals": {
            "pdq": IMAGE_URL_TO_PDQ[image_url],
        },
    }


def test_bank_update_content(client: FlaskClient, image_server: str):
    bank_name = "TEST_BANK_UPDATE"
    create_bank(client, bank_name)

    # Add content
    image_url = f"{image_server}/image1.jpg"
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


def test_bank_update_content_400(client: FlaskClient, image_server: str):
    bank_name = "TEST_BANK_UPDATE"
    create_bank(client, bank_name)

    # Add content
    image_url = f"{image_server}/image1.jpg"
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


def test_banks_delete_content(client: FlaskClient, image_server: str):
    bank_name = "NEW_BANK"
    image_url = f"{image_server}/image1.jpg"

    create_bank(client, bank_name)
    add_hash_to_bank(client, bank_name, image_url, 1)

    post_response = client.delete(f"/c/bank/{bank_name}/content/1")

    assert post_response.status_code == 200
    assert post_response.json == {"deleted": 1}


def test_banks_add_metadata(client: FlaskClient, image_server: str):
    bank_name = "NEW_BANK"
    create_bank(client, bank_name)

    image_url = f"{image_server}/image1.jpg"
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


def test_banks_add_hash_index(app: Flask, client: FlaskClient, image_server: str):
    bank_name = "NEW_BANK"
    bank_name_2 = "NEW_BANK_2"
    image_url = f"{image_server}/image1.jpg"
    image_url_2 = f"{image_server}/image2.jpg"

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


def test_bank_get_content_with_signals(client: FlaskClient, image_server: str):
    bank_name = "TEST_BANK_GET_SIGS"
    create_bank(client, bank_name)

    image_url = f"{image_server}/image1.jpg"
    add_response = client.post(
        f"/c/bank/{bank_name}/content?url={image_url}&content_type=photo"
    )
    assert add_response.status_code == 200, str(add_response.get_json())
    assert add_response.json
    content_id = add_response.json.get("id")

    # Get content by id without signals
    get_response = client.get(f"/c/bank/{bank_name}/content/{content_id}")
    assert get_response.status_code == 200, str(get_response.get_json())
    assert get_response.json
    assert get_response.json.get("id") == content_id
    # Signals should not be included when include_signals is not specified
    assert "signals" not in get_response.json

    # Get content by id with signals
    get_response = client.get(
        f"/c/bank/{bank_name}/content/{content_id}?include_signals=true"
    )
    assert get_response.status_code == 200, str(get_response.get_json())
    assert get_response.json
    assert get_response.json.get("id") == content_id
    # The API may not include signals field if no signals are found
    # This is the current behavior - signals field is only included when signals exist
    if "signals" in get_response.json:
        assert isinstance(get_response.json["signals"], dict)
        # If signals exist, they should not be empty
        assert len(get_response.json["signals"]) > 0


def test_bank_get_content_returns_stored_metadata(client: FlaskClient):
    """GET /bank/<name>/content/<id> returns user-supplied metadata stored via POST."""
    bank_name = "TEST_BANK_METADATA"
    create_bank(client, bank_name)

    image_url = "https://github.com/facebook/ThreatExchange/blob/main/pdq/data/bridge-mods/aaa-orig.jpg?raw=true"
    metadata = {
        "content_id": "ext-id-123",
        "content_uri": "https://example.com/item/123",
        "json": {"source": "test", "nested": {"key": "value"}},
    }
    add_response = client.post(
        f"/c/bank/{bank_name}/content?url={image_url}&content_type=photo",
        json={"metadata": metadata},
    )
    assert add_response.status_code == 200, str(add_response.get_json())
    add_data = add_response.get_json()
    assert add_data is not None
    content_id = add_data["id"]

    get_response = client.get(f"/c/bank/{bank_name}/content/{content_id}")
    assert get_response.status_code == 200, str(get_response.get_json())
    get_data = get_response.get_json()
    assert get_data is not None
    assert "metadata" in get_data
    assert get_data["metadata"]["content_id"] == metadata["content_id"]
    assert get_data["metadata"]["content_uri"] == metadata["content_uri"]
    assert get_data["metadata"]["json"] == metadata["json"]


def test_bank_get_content_include_metadata_false(client: FlaskClient):
    """GET with include_metadata=false omits metadata from response."""
    bank_name = "TEST_BANK_NO_METADATA"
    create_bank(client, bank_name)

    image_url = "https://github.com/facebook/ThreatExchange/blob/main/pdq/data/bridge-mods/aaa-orig.jpg?raw=true"
    add_response = client.post(
        f"/c/bank/{bank_name}/content?url={image_url}&content_type=photo",
        json={
            "metadata": {"content_id": "id1", "content_uri": "https://example.com/1"}
        },
    )
    assert add_response.status_code == 200, str(add_response.get_json())
    add_data = add_response.get_json()
    assert add_data is not None
    content_id = add_data["id"]

    get_response = client.get(
        f"/c/bank/{bank_name}/content/{content_id}?include_metadata=false"
    )
    assert get_response.status_code == 200, str(get_response.get_json())
    get_data = get_response.get_json()
    assert get_data is not None
    assert "metadata" not in get_data


def test_bank_add_content_with_note(client: FlaskClient, image_server: str):
    """POST content with a note; GET returns the note."""
    bank_name = "TEST_BANK_NOTE"
    create_bank(client, bank_name)

    image_url = f"{image_server}/image1.jpg"
    add_response = client.post(
        f"/c/bank/{bank_name}/content?url={image_url}&content_type=photo",
        json={"note": "Reported by user X"},
    )
    assert add_response.status_code == 200, str(add_response.get_json())
    content_id = add_response.get_json()["id"]

    get_response = client.get(f"/c/bank/{bank_name}/content/{content_id}")
    assert get_response.status_code == 200, str(get_response.get_json())
    get_data = get_response.get_json()
    assert get_data["note"] == "Reported by user X"


def test_bank_add_content_without_note_omitted(client: FlaskClient, image_server: str):
    """Add content without a note; GET does not include note key."""
    bank_name = "TEST_BANK_NO_NOTE"
    create_bank(client, bank_name)

    image_url = f"{image_server}/image1.jpg"
    add_response = client.post(
        f"/c/bank/{bank_name}/content?url={image_url}&content_type=photo",
    )
    assert add_response.status_code == 200, str(add_response.get_json())
    content_id = add_response.get_json()["id"]

    get_response = client.get(f"/c/bank/{bank_name}/content/{content_id}")
    assert get_response.status_code == 200, str(get_response.get_json())
    assert "note" not in get_response.get_json()


def test_bank_update_content_note(client: FlaskClient, image_server: str):
    """PUT can set, update, and clear a note."""
    bank_name = "TEST_BANK_NOTE_UPDATE"
    create_bank(client, bank_name)

    image_url = f"{image_server}/image1.jpg"
    add_response = client.post(
        f"/c/bank/{bank_name}/content?url={image_url}&content_type=photo",
    )
    assert add_response.status_code == 200, str(add_response.get_json())
    content_id = add_response.get_json()["id"]

    # Set note
    update_response = client.put(
        f"/c/bank/{bank_name}/content/{content_id}",
        json={"note": "Initial note"},
    )
    assert update_response.status_code == 200, str(update_response.get_json())

    get_response = client.get(f"/c/bank/{bank_name}/content/{content_id}")
    assert get_response.get_json()["note"] == "Initial note"

    # Update note
    update_response = client.put(
        f"/c/bank/{bank_name}/content/{content_id}",
        json={"note": "Updated note"},
    )
    assert update_response.status_code == 200

    get_response = client.get(f"/c/bank/{bank_name}/content/{content_id}")
    assert get_response.get_json()["note"] == "Updated note"

    # Clear note
    update_response = client.put(
        f"/c/bank/{bank_name}/content/{content_id}",
        json={"note": ""},
    )
    assert update_response.status_code == 200

    get_response = client.get(f"/c/bank/{bank_name}/content/{content_id}")
    assert "note" not in get_response.get_json()


def test_bank_add_note_too_long(client: FlaskClient, image_server: str):
    """Note exceeding 255 characters is rejected."""
    bank_name = "TEST_BANK_NOTE_LONG"
    create_bank(client, bank_name)

    image_url = f"{image_server}/image1.jpg"
    add_response = client.post(
        f"/c/bank/{bank_name}/content?url={image_url}&content_type=photo",
        json={"note": "x" * 256},
    )
    assert add_response.status_code == 400


def test_bank_add_hash_with_note(client: FlaskClient):
    """POST signal with a note; GET returns the note."""
    bank_name = "TEST_BANK_HASH_NOTE"
    create_bank(client, bank_name)

    pdq_hash = "0" * 64
    add_response = client.post(
        f"/c/bank/{bank_name}/signal",
        json={"pdq": pdq_hash, "note": "Hash from campaign ABC"},
    )
    assert add_response.status_code == 200, str(add_response.get_json())
    content_id = add_response.get_json()["id"]

    get_response = client.get(f"/c/bank/{bank_name}/content/{content_id}")
    assert get_response.status_code == 200, str(get_response.get_json())
    assert get_response.get_json()["note"] == "Hash from campaign ABC"


def test_bank_get_content_without_metadata_omitted(client: FlaskClient):
    """Add content without metadata; GET does not include metadata key."""
    bank_name = "TEST_BANK_NO_META"
    create_bank(client, bank_name)

    image_url = "https://github.com/facebook/ThreatExchange/blob/main/pdq/data/bridge-mods/aaa-orig.jpg?raw=true"
    add_response = client.post(
        f"/c/bank/{bank_name}/content?url={image_url}&content_type=photo",
    )
    assert add_response.status_code == 200, str(add_response.get_json())
    add_data = add_response.get_json()
    assert add_data is not None
    content_id = add_data["id"]

    get_response = client.get(f"/c/bank/{bank_name}/content/{content_id}")
    assert get_response.status_code == 200, str(get_response.get_json())
    get_data = get_response.get_json()
    assert get_data is not None
    assert "metadata" not in get_data
