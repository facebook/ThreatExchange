# Copyright (c) Meta Platforms, Inc. and affiliates.

import os
import sys

import flask
import flask_migrate
import flask_sqlalchemy

db = flask_sqlalchemy.SQLAlchemy()
migrate = flask_migrate.Migrate()


def create_app():
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
    app.db = db

    db.init_app(app)
    migrate.init_app(app, db)

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
    from .blueprints import hashing, matching, curation

    if app.config.get("ROLE_HASHER", False):
        app.register_blueprint(hashing.bp, url_prefix="/h")

    if app.config.get("ROLE_MATCHER", False):
        app.register_blueprint(matching.bp, url_prefix="/m")

    if app.config.get("ROLE_CURATOR", False):
        app.register_blueprint(curation.bp, url_prefix="/c")

    from . import models

    @app.cli.command("seed")
    def seed_data():
        # TODO: This is a placeholder for where some useful seed data can be loaded;
        # particularly important for development
        bank = models.Bank(name="bad_stuff", enabled=True)
        db.session.add(bank)
        db.session.commit()

    return app
