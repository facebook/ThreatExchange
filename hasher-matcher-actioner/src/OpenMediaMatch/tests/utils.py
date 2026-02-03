# Copyright (c) Meta Platforms, Inc. and affiliates.

import os
import pytest
import typing as t

from flask import Flask
from flask.testing import FlaskClient

from threatexchange.exchanges.impl.static_sample import StaticSampleSignalExchangeAPI

from OpenMediaMatch.app import create_app
from OpenMediaMatch.persistence import get_storage
from OpenMediaMatch.storage.postgres.flask_utils import reset_tables
from OpenMediaMatch.storage.postgres import database
from sqlalchemy.sql import text

IMAGE_URL_TO_PDQ = {
    "https://github.com/facebook/ThreatExchange/blob/main/pdq/data/bridge-mods/aaa-orig.jpg?raw=true": "f8f8f0cee0f4a84f06370a22038f63f0b36e2ed596621e1d33e6b39c4e9c9b22",
    "https://github.com/facebook/ThreatExchange/blob/main/pdq/data/misc-images/c.png?raw=true": "e64cc9d91c623882f8d1f1d9a398e78c9f199b3bd83924f2b7e11e0bf861b064",
}


@pytest.fixture()
def app() -> t.Iterator[Flask]:
    os.environ.setdefault("OMM_CONFIG", "tests/omm_config.py")
    app = create_app()

    with app.app_context():
        # If we want to try and re-use the database between tests,
        # there's a way to push a context that will undo all commits.
        # For now, drop and recreate is a fast way to do it.
        reset_tables()

        # Sanity check
        assert (
            database.db.session.execute(
                text("SELECT count(1) FROM pg_largeobject_metadata;")
            ).scalar_one()
            == 0
        ), "Leaking large objects!"

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


def add_hash_to_bank(
    client: FlaskClient, bank_name: str, image_url: str, content_id: int = 1
):
    post_response = client.post(
        "/c/bank/{}/content?url={}&content_type=photo".format(bank_name, image_url)
    )

    assert post_response.status_code == 200
    assert post_response.json == {
        "id": content_id,
        "signals": {
            "pdq": IMAGE_URL_TO_PDQ[image_url],
        },
    }
