# Copyright (c) Meta Platforms, Inc. and affiliates.

import logging
import pathlib

import flask_migrate
from flask import Flask

import OpenMediaMatch
from OpenMediaMatch.tests.utils import app  # noqa: F401


def test_running_migrations_keeps_existing_loggers(app: Flask) -> None:
    existing = logging.getLogger("OpenMediaMatch.tests.existing_logger")
    migrations_dir = str(pathlib.Path(OpenMediaMatch.__file__).parent / "migrations")
    flask_migrate.current(directory=migrations_dir)  # Runs env.py
    assert not existing.disabled
