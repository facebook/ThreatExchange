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
        # I'm sorry future person, I don't know how to keep the
        # test database clean without affecting the the prod instance
        database.db.drop_all()
        database.db.create_all()

    yield app


@pytest.fixture()
def client(app) -> FlaskClient:
    return app.test_client()
