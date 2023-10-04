import os
import pytest
import typing as t

from flask import Flask
from flask.testing import FlaskClient

from OpenMediaMatch.app import create_app
from OpenMediaMatch import database


@pytest.fixture()
def app() -> t.Iterator[Flask]:
    os.environ.setdefault("OMM_CONFIG", "tests/omm_config.py")
    app = create_app()

    with app.app_context():
        # If we want to try and re-use the database between tests,
        # there's a way to push a context that will undo all commits.
        # For now, drop and recreate is a fast way to do it.
        database.db.drop_all()
        database.db.create_all()

        yield app


@pytest.fixture()
def client(app) -> FlaskClient:
    return app.test_client()


def create_bank(client: FlaskClient, bank_name: str):
    post_response = client.post(
        "/c/banks",
        json={"name": bank_name},
    )
    assert post_response.status_code == 201
    assert post_response.json == {"matching_enabled_ratio": 1.0, "name": bank_name}

def add_hash_to_bank(client: FlaskClient, bank_name: str, image_url: str):
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