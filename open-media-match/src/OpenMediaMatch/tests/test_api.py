from flask.testing import FlaskClient
from OpenMediaMatch.tests.utils import app, client, create_bank


def test_status_response(client: FlaskClient):
    response = client.get("/status")
    assert response.status_code == 200
    assert response.data == b"I-AM-ALIVE\n"


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

    post_response = client.put(
        "/c/bank/MY_TEST_BANK",
        json={"name": "MY_TEST_BANK_RENAMED"},
    )
    assert post_response.status_code == 200
    assert post_response.get_json()["name"] == "MY_TEST_BANK_RENAMED"


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


def test_banks_add_hash(client: FlaskClient):
    bank_name = "NEW_BANK"
    create_bank(client, bank_name)

    image_url = "https://github.com/facebook/ThreatExchange/blob/main/pdq/data/bridge-mods/aaa-orig.jpg?raw=true"

    post_response = client.post(
        "/c/bank/{}/content?url={}&content_type=photo".format(bank_name, image_url)
    )

    assert post_response.status_code == 200
    assert post_response.json == {
        "id": 1,
        "signals": {
            "pdq": "f8f8f0cee0f4a84f06370a22038f63f0b36e2ed596621e1d33e6b39c4e9c9b22"
        },
    }
