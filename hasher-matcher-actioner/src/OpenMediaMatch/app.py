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
import typing as t

import click
import flask
from flask.logging import default_handler
from flask_apscheduler import APScheduler

from threatexchange.exchanges import auth
from threatexchange.exchanges.signal_exchange_api import TSignalExchangeAPICls

from OpenMediaMatch.storage import interface
from OpenMediaMatch.storage.postgres.impl import DefaultOMMStore
from OpenMediaMatch.background_tasks import (
    build_index,
    fetcher,
    development as dev_apscheduler,
)
from OpenMediaMatch.persistence import get_storage
from OpenMediaMatch.blueprints import development, hashing, matching, curation, ui
from OpenMediaMatch.utils import dev_utils


def _is_debug_mode():
    """Does it look like the app is being run in debug mode?"""
    debug = os.environ.get("FLASK_DEBUG")
    if not debug:
        return os.environ.get("FLASK_ENV") == "development"
    return debug.lower() not in ("0", "false", "no")


def _is_werkzeug_reloaded_process():
    """If in debug mode, are we in the reloaded process?"""
    return os.environ.get("WERKZEUG_RUN_MAIN") == "true"


def _setup_task_logging(app_logger: logging.Logger):
    """Clownily replace module loggers with our own"""
    fetcher.logger = app_logger.getChild("Fetcher")
    build_index.logger = app_logger.getChild("Indexer")


def create_app() -> flask.Flask:
    """
    Create and configure the Flask app
    """

    # We like the flask logging format, so lets have it everywhere
    root = logging.getLogger()
    if not root.handlers:
        root.addHandler(default_handler)
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

    engine_logging = app.config.get("SQLALCHEMY_ENGINE_LOG_LEVEL")
    if engine_logging is not None:
        logging.getLogger("sqlalchemy.engine").setLevel(engine_logging)

    if "STORAGE_IFACE_INSTANCE" not in app.config:
        app.logger.warning("No storage class provided, using the default")
        app.config["STORAGE_IFACE_INSTANCE"] = DefaultOMMStore()
    storage = app.config["STORAGE_IFACE_INSTANCE"]
    assert isinstance(
        storage, interface.IUnifiedStore
    ), "STORAGE_IFACE_INSTANCE is not an instance of IUnifiedStore"

    _setup_task_logging(app.logger)

    scheduler: APScheduler | None = None

    with app.app_context():
        # We only run apscheduler in the "outer" reloader process, else we'll
        # have multiple executions of the the scheduler in debug mode
        if _is_werkzeug_reloaded_process():
            now = datetime.datetime.now()
            scheduler = dev_apscheduler.get_apscheduler()
            scheduler.init_app(app)
            tasks = []
            if app.config.get("TASK_FETCHER", False):
                tasks.append("Fetcher")
                scheduler.add_job(
                    "Fetcher",
                    fetcher.apscheduler_fetch_all,
                    trigger="interval",
                    seconds=60 * 4,
                    start_date=now + datetime.timedelta(seconds=30),
                )
            if app.config.get("TASK_INDEXER", False):
                tasks.append("Indexer")
                scheduler.add_job(
                    "Indexer",
                    build_index.apscheduler_build_all_indices,
                    trigger="interval",
                    seconds=60,
                    start_date=now + datetime.timedelta(seconds=15),
                )
            app.logger.info("Started Apscheduler, initial tasks: %s", tasks)
            scheduler.start()

        storage.init_flask(app)

        is_production = app.config.get("PRODUCTION", True)
        # Register Flask blueprints for whichever server roles are enabled...
        # URL prefixing facilitates easy Layer 7 routing :)

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
            if app.config.get("TASK_INDEX_CACHE", False):
                matching.initiate_index_cache(app, scheduler)

        if app.config.get("ROLE_CURATOR", False):
            app.register_blueprint(curation.bp, url_prefix="/c")

    @app.route("/")
    def home():
        dst = "status" if is_production else "ui"
        return flask.redirect(f"/{dst}")

    @app.route("/status")
    def status():
        """
        Liveness/readiness check endpoint for your favourite Layer 7 load balancer
        """
        if app.config.get("ROLE_MATCHER", False):
            if matching.index_cache_is_stale():
                return f"INDEX-STALE", 503
        return "I-AM-ALIVE", 200

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

    @app.cli.command("seed")
    def seed_data() -> None:
        """Add sample data API connection"""
        dev_utils.seed_sample()

    @app.cli.command("big-seed")
    @click.option("-b", "--banks", default=100, show_default=True)
    @click.option("-s", "--seeds", default=10000, show_default=True)
    def seed_enourmous(banks: int, seeds: int) -> None:
        """
        Seed the database with a large number of banks and hashes
        It will generate n banks and put n/m hashes on each bank
        """
        dev_utils.seed_banks_random(banks, seeds)

    @app.cli.command("fetch")
    def fetch():
        """Run the 'background task' to fetch from 3p data and sync to local banks"""
        app.logger.setLevel(logging.DEBUG)
        storage = get_storage()
        fetcher.fetch_all(
            storage,
            storage.get_signal_type_configs(),
        )

    @app.cli.command("build_indices")
    def build_indices():
        """Run the 'background task' to rebuild indices from bank contents"""
        app.logger.setLevel(logging.DEBUG)
        storage = get_storage()
        build_index.build_all_indices(storage, storage, storage)

    @app.cli.command("auth")
    @click.argument("api_name", callback=_get_api_cfg)
    @click.option(
        "--from-str",
        help="attempt to use the private _from_str method to auth",
    )
    @click.option("--unset", is_flag=True, help="clear credentials")
    def set_credentials(
        api_name: interface.SignalExchangeAPIConfig, from_str: str | None, unset: bool
    ) -> None:
        """
        Persist credentials for apis.

        Using the lookup mechanisms built into threatexchange.exchange.auth
        attempt to find credentials in the local environment.

        The easiest way is usually via an environment variable.

        Example, for fb_threatexchange:

          TX_ACCESS_TOKEN='12345678|facefaceface' flask auth
        """
        api_cfg = api_name  # Can't rename arguments, so we rename variable :/
        storage = get_storage()
        api_cls = api_cfg.api_cls
        cred_cls: auth.CredentialHelper = api_cls.get_credential_cls()  # type: ignore

        if unset:
            api_cfg.credentials = None
        else:
            if from_str is not None:
                creds = cred_cls._from_str(from_str)
                if creds is None or not creds._are_valid():
                    raise click.UsageError("Invalid 'from-str'")
            else:
                try:
                    creds = cred_cls.get(api_cls)
                except auth.SignalExchangeAPIMissingAuthException as e:
                    raise click.UsageError(e.pretty_str())
                except auth.SignalExchangeAPIInvalidAuthException as e:
                    raise click.UsageError(e.message)
            api_cfg.credentials = creds
        storage.exchange_api_config_update(api_cfg)

    return app


def _get_api_cfg(ctx: click.Context, param: click.Parameter, value: str):
    storage = get_storage()
    config = storage.exchange_apis_get_configs().get(value)
    if config is None:
        raise click.BadParameter("No such api")
    api_cls = config.api_cls
    if not issubclass(api_cls, auth.SignalExchangeWithAuth):
        raise click.BadParameter("api doesn't take authentification")
    return config
