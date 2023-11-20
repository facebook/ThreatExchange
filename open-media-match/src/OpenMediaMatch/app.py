# Copyright (c) Meta Platforms, Inc. and affiliates.

# NO IMPORTS ABOVE ME
# Import pdq first with its hash order warning squelched, it's before our time
import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from threatexchange.signal_type.pdq import signal as _
## Resume regularly scheduled imports

import logging
import os
import datetime
import sys
import random
import typing as t

import click
import flask

from OpenMediaMatch.storage.interface import IUnifiedStore
from OpenMediaMatch.storage.postgres.impl import DefaultOMMStore
from OpenMediaMatch.background_tasks import (
    build_index,
    fetcher,
    development as dev_apscheduler,
)
from OpenMediaMatch.persistence import get_storage
from OpenMediaMatch.blueprints import development, hashing, matching, curation, ui
from OpenMediaMatch.storage.interface import BankConfig

from threatexchange.signal_type.signal_base import SignalType
from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal


def _is_debug_mode():
    """Does it look like the app is being run in debug mode?"""
    debug = os.environ.get("FLASK_DEBUG")
    if not debug:
        return os.environ.get("FLASK_ENV") == "development"
    return debug.lower() not in ("0", "false", "no")


def _is_dbg_werkzeug_reloaded_process():
    """If in debug mode, are we in the reloaded process?"""
    if not _is_debug_mode():
        return False
    return os.environ.get("WERKZEUG_RUN_MAIN") == "true"


def _setup_task_logging(app_logger: logging.Logger):
    """Clownily replace module loggers with our own"""
    fetcher.logger = app_logger.getChild("Fetcher")
    build_index.logger = app_logger.getChild("Indexer")


def create_app() -> flask.Flask:
    """
    Create and configure the Flask app
    """

    app = flask.Flask(__name__)

    if "OMM_CONFIG" in os.environ:
        app.config.from_envvar("OMM_CONFIG")
    elif sys.argv[0].endswith("/flask"):  # Default for flask CLI
        # The devcontainer settings. If you are using the CLI outside
        # the devcontainer and getting an error, just override the env
        app.config.from_pyfile("/workspace/.devcontainer/omm_config.py")
    else:
        raise RuntimeError("No flask config given - try populating OMM_CONFIG env")
    app.config.update(
        SQLALCHEMY_DATABASE_URI=app.config.get("DATABASE_URI"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    # Probably better to move this into a more normal looking default config
    storage_cls = t.cast(
        t.Type[IUnifiedStore], app.config.get("storage_cls", DefaultOMMStore)
    )
    app.config["storage_instance"] = storage_cls.init_flask(app)

    _setup_task_logging(app.logger)

    is_production = app.config.get("PRODUCTION", True)

    @app.route("/")
    def home():
        dst = "status" if is_production else "ui"
        return flask.redirect(f"/{dst}")

    @app.route("/status")
    def status():
        """
        Liveness/readiness check endpoint for your favourite Layer 7 load balancer
        """
        storage = get_storage()
        if not storage.is_ready():
            return "NOT-READY", 503
        return "I-AM-ALIVE\n", 200

    @app.route("/site-map")
    def site_map():
        # Use a set to avoid duplicates (e.g. same path, multiple methods)
        routes = set()
        for rule in app.url_map.iter_rules():
            routes.add(rule.rule)
        # Convert set to a list so we can sort it.
        routes = list(routes)
        routes.sort()
        return routes

    # Register Flask blueprints for whichever server roles are enabled...
    # URL prefixing facilitates easy Layer 7 routing :)
    # Linters complain about imports off the top level, but this is needed
    # to prevent circular imports

    if (
        not is_production
        and app.config.get("ROLE_HASHER", False)
        and app.config.get("ROLE_MATCHER", False)
    ):
        app.register_blueprint(development.bp, url_prefix="/dev")
        app.register_blueprint(ui.bp, url_prefix="/ui")

    if app.config.get("ROLE_HASHER", False):
        app.register_blueprint(hashing.bp, url_prefix="/h")

    if app.config.get("ROLE_MATCHER", False):
        app.register_blueprint(matching.bp, url_prefix="/m")

    if app.config.get("ROLE_CURATOR", False):
        app.register_blueprint(curation.bp, url_prefix="/c")

    @app.cli.command("seed")
    def seed_data():
        """Insert plausible-looking data into the database layer"""
        from threatexchange.signal_type.pdq.signal import PdqSignal

        bank_name = "SEED_BANK"

        storage = get_storage()
        storage.bank_update(BankConfig(name=bank_name, matching_enabled_ratio=1.0))

        for st in (PdqSignal, VideoMD5Signal):
            for example in st.get_examples():
                storage.bank_add_content(bank_name, {st.get_name(): example})

    @app.cli.command("seed_enourmous")
    @click.option("-b", "--banks", default=100, show_default=True)
    @click.option("-s", "--seeds", default=10000, show_default=True)
    def seed_enourmous(banks: int, seeds: int) -> None:
        """
        Seed the database with a large number of banks and hashes
        It will generate n banks and put n/m hashes on each bank
        """
        storage = get_storage()

        types: list[t.Type[SignalType]] = [PdqSignal, VideoMD5Signal]

        for i in range(banks):
            # create bank
            bank = BankConfig(name=f"SEED_BANK_{i}", matching_enabled_ratio=1.0)
            storage.bank_update(bank, create=True)

            # Add hashes
            for _ in range(seeds // banks):
                # grab randomly either PDQ or MD5 signal
                signal_type = random.choice(types)
                random_hash = signal_type.generate_random_hash()  # type: ignore[attr-defined]

                storage.bank_add_content(bank.name, {signal_type: random_hash})

            print("Finished adding hashes to", bank.name)

    @app.cli.command("fetch")
    def fetch():
        """Run the 'background task' to fetch from 3p data and sync to local banks"""
        storage = get_storage()
        fetcher.fetch_all(
            storage,
            {
                st.signal_type.get_name(): st.signal_type
                for st in storage.get_signal_type_configs().values()
            },
        )

    @app.cli.command("build_indices")
    def build_indices():
        """Run the 'background task' to rebuild indices from bank contents"""
        storage = get_storage()
        build_index.build_all_indices(storage, storage, storage)

    with app.app_context():
        # We only want to run apscheduler in debug mode
        # and only in the "outer" reloader process
        if _is_dbg_werkzeug_reloaded_process():
            app.logger.critical(
                "DEVELOPMENT: Started background tasks with apscheduler."
            )

            now = datetime.datetime.now()
            scheduler = dev_apscheduler.get_apscheduler()
            scheduler.init_app(app)
            scheduler.add_job(
                "Fetcher",
                fetcher.apscheduler_fetch_all,
                trigger="interval",
                seconds=60 * 4,
                start_date=now + datetime.timedelta(seconds=30),
            )
            scheduler.add_job(
                "Indexer",
                build_index.apscheduler_build_all_indices,
                trigger="interval",
                seconds=60,
                start_date=now + datetime.timedelta(seconds=15),
            )
            scheduler.start()

    return app
