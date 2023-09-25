# Copyright (c) Meta Platforms, Inc. and affiliates.

import logging
import os
import sys
import warnings

import flask
from flask.logging import default_handler
import flask_migrate

# Import pdq first with its hash order warning squelched, it's before our time
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from threatexchange.signal_type.pdq import signal as _

from OpenMediaMatch import database
from OpenMediaMatch.background_tasks import build_index, fetcher
from OpenMediaMatch.persistence import get_storage
from OpenMediaMatch.blueprints import hashing, matching, curation


def create_app():
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

    @app.route("/")
    def index():
        """
        Sanity check endpoint showing a basic status page
        TODO: in development mode, this could show some useful additional info
        """
        return flask.render_template(
            "index.html.j2", production=app.config.get("PRODUCTION")
        )

    @app.route("/status")
    def status():
        """
        Liveness/readiness check endpoint for your favourite Layer 7 load balancer
        """
        return "I-AM-ALIVE\n"

    # Register Flask blueprints for whichever server roles are enabled...
    # URL prefixing facilitates easy Layer 7 routing :)
    # Linters complain about imports off the top level, but this is needed
    # to prevent circular imports

    if app.config.get("ROLE_HASHER", False):
        app.register_blueprint(hashing.bp, url_prefix="/h")

    if app.config.get("ROLE_MATCHER", False):
        app.register_blueprint(matching.bp, url_prefix="/m")

    if app.config.get("ROLE_CURATOR", False):
        app.register_blueprint(curation.bp, url_prefix="/c")

    @app.cli.command("seed")
    def seed_data():
        """Insert plausible-looking data into the database layer"""
        # TODO: This is a placeholder for where some useful seed data can be loaded;
        # particularly important for development
        bank = database.Bank(name="bad_stuff", enabled=True)
        database.db.session.add(bank)
        database.db.session.commit()

    @app.cli.command("fetch")
    def fetch():
        """Run the 'background task' to fetch from 3p data and sync to local banks"""
        storage = get_storage()
        task_logger = logging.getLogger(fetcher.__name__)
        task_logger.addHandler(default_handler)
        task_logger.setLevel(logging.NOTSET)
        logging.getLogger().setLevel(logging.NOTSET)
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
        task_logger = logging.getLogger(build_index.__name__)
        task_logger.addHandler(default_handler)
        task_logger.setLevel(logging.NOTSET)
        logging.getLogger().setLevel(logging.NOTSET)
        build_index.build_all_indices(storage, None, storage)

    return app
