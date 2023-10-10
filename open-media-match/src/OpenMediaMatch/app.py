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

import flask
from flask.logging import default_handler
import flask_migrate

from OpenMediaMatch import database
from OpenMediaMatch.background_tasks import (
    build_index,
    fetcher,
    development as dev_apscheduler,
)
from OpenMediaMatch.persistence import get_storage
from OpenMediaMatch.blueprints import development, hashing, matching, curation, ui
from OpenMediaMatch.storage.interface import BankConfig

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

    migrate = flask_migrate.Migrate()

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

    database.db.init_app(app)
    migrate.init_app(app, database.db)

    _setup_task_logging(app.logger)

    is_production = app.config.get("PRODUCTION", True)

    # TODO - move me into ui blueprints
    @app.route("/")
    def home():
        """
        Sanity check endpoint showing a basic status page
        """
        signaltypes = curation.get_all_signal_types()
        contenttypes = curation.get_all_content_types()
        banks = curation.banks_index()

        return flask.render_template(
            "index.html.j2",
            production=is_production,
            signal=signaltypes,
            content=contenttypes,
            bankList=banks,
        )

    @app.route("/status")
    def status():
        """
        Liveness/readiness check endpoint for your favourite Layer 7 load balancer
        """
        return "I-AM-ALIVE\n"

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

    @app.cli.command("create_tables")
    def create_tables():
        """Create all the tables based on the database module"""
        with app.app_context():
            database.db.create_all()

    @app.cli.command("table_stats")
    def table_stats():
        """Simple stats about the database"""
        with app.app_context():
            print("Banks:", database.Bank.query.count())
            print("Contents:", database.BankContent.query.count())
            print("Signals/Hashes:", database.ContentSignal.query.count())
            print("Signals/Index:", database.SignalIndex.query.count())

    @app.cli.command("reset_all_tables")
    def reset_tables():
        """Clears all the tables and recreates them"""
        with app.app_context():
            database.db.drop_all()
            database.db.create_all()

    @app.cli.command("seed")
    def seed_data():
        """Insert plausible-looking data into the database layer"""
        from threatexchange.signal_type.pdq.signal import PdqSignal

        bankName = "TEST_BANK"
        contentList = []
        for example in PdqSignal.get_examples():
            contentList.append(
                database.BankContent(
                    signals=[
                        database.ContentSignal(
                            signal_type=PdqSignal.get_name(),
                            signal_val=example,
                        )
                    ]
                )
            )
        bank = database.Bank(
            name=bankName,
            content=contentList,
        )

        database.db.session.add(bank)
        database.db.session.commit()

    @app.cli.command("seed_enourmous")
    def seed_enourmous():
        """
        Seed the database with a large number of banks and hashes
        run command with:
        export OMM_SEED_BANKS=100
        export OMM_SEED_HASHES=10000
        or OMM_SEED_BANKS=100 OMM_SEED_HASHES=10000 flask seed_enourmous
        It will generate n banks and put n/m hashes on each bank
        """
        # read from env for how many hashes to add\
        banks_to_add = int(os.environ.get("OMM_SEED_BANKS", 100))
        hashes_to_add = int(os.environ.get("OMM_SEED_HASHES", 10000))
        storage = get_storage()

        for i in range(banks_to_add):
            # create bank
            bank = BankConfig(name=f"TEST_BANK_{i}", matching_enabled_ratio=1.0)
            storage.bank_update(bank, create=True)

            # Add hashes
            for _ in range(hashes_to_add // banks_to_add):
                # grab randomly either PDQ or MD5 signal
                signal_type = random.choice([PdqSignal, VideoMD5Signal])
                random_hash = signal_type.generate_random_hash()

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
