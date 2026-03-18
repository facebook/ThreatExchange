# Copyright (c) Meta Platforms, Inc. and affiliates.

import functools
import http.server
import os
import shutil
import tempfile
import threading
import typing as t
from pathlib import Path

import pytest
from PIL import Image

from flask import Flask
from flask.testing import FlaskClient

from threatexchange.exchanges.impl.static_sample import StaticSampleSignalExchangeAPI
from threatexchange.signal_type.pdq.signal import PdqSignal

from OpenMediaMatch.app import create_app
from OpenMediaMatch.persistence import get_storage
from OpenMediaMatch.storage.postgres.flask_utils import reset_tables
from OpenMediaMatch.storage.postgres import database
from sqlalchemy.sql import text

# Populated at session start by the image_server fixture
IMAGE_URL_TO_PDQ: dict[str, str] = {}


@pytest.fixture(scope="session", autouse=True)
def image_server() -> t.Iterator[str]:
    """Start a local HTTP server serving test images, avoiding external HTTP calls.

    Populates IMAGE_URL_TO_PDQ with computed PDQ hashes for each served image.
    Yields the base URL (e.g. "http://127.0.0.1:PORT").
    """
    tmpdir = Path(tempfile.mkdtemp())
    try:
        def make_checkerboard(cell: int) -> Image.Image:
            img = Image.new("RGB", (128, 128))
            pixels = img.load()
            assert pixels is not None
            for x in range(128):
                for y in range(128):
                    pixels[x, y] = (255, 255, 255) if (x // cell + y // cell) % 2 else (0, 0, 0)
            return img

        # Two checkerboards with different cell sizes → different PDQ hashes
        make_checkerboard(cell=8).save(tmpdir / "image1.jpg", format="JPEG")
        make_checkerboard(cell=16).save(tmpdir / "image2.jpg", format="JPEG")

        handler = functools.partial(
            http.server.SimpleHTTPRequestHandler, directory=str(tmpdir)
        )
        server = http.server.HTTPServer(("127.0.0.1", 0), handler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        base_url = f"http://127.0.0.1:{port}"
        for filename in ("image1.jpg", "image2.jpg"):
            url = f"{base_url}/{filename}"
            IMAGE_URL_TO_PDQ[url] = PdqSignal.hash_from_file(tmpdir / filename)

        yield base_url
    finally:
        server.shutdown()
        shutil.rmtree(tmpdir)


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
