import os
import pytest

from OpenMediaMatch.app import create_app


@pytest.fixture()
def app():
    os.environ.setdefault("OMM_CONFIG", "tests/omm_config.py")
    app = create_app()

    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_status_response(client):
    response = client.get("/status")
    assert response.status_code == 200
    assert response.data == b"I-AM-ALIVE\n"
