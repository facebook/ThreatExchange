# Copyright (c) Meta Platforms, Inc. and affiliates.

import os
import flask


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
        app.config.get('PRODUCTION')
        return flask.render_template('index.html.j2')

    @app.route('/status')
    def status():
        """
        Liveness/readiness check endpoint for your favourite Layer 7 load balancer
        """
        return 'I-AM-ALIVE\n'

    @app.route('/hash/image')
    def hash_image():
        """
        Hash an image
        """
        image_url = flask.request.args.get('url')
        if image_url is None:
            flask.abort(400)

        return f"If this was implemented you'd be seeing the PDQ hash of the image at {image_url} here"

    return app
