# Copyright (c) Meta Platforms, Inc. and affiliates.

import os
import flask

from . import hashing

def create_app():
    """
    Create and configure the Flask app
    """
    app = flask.Flask(__name__)
    app.config.from_envvar('OMM_CONFIG')

    @app.route('/')
    def index():
        """
        Sanity check endpoint showing a basic status page
        TODO: in development mode, this could show some useful additional info
        """
        return flask.render_template('index.html.j2', production=app.config.get('PRODUCTION'))

    @app.route('/status')
    def status():
        """
        Liveness/readiness check endpoint for your favourite Layer 7 load balancer
        """
        return 'I-AM-ALIVE\n'

    app.register_blueprint(hashing.bp)

    return app
