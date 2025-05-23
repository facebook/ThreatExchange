# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
OpenAPI specification and documentation endpoints for HMA.
"""

import os
# import yaml # PyYAML no longer needed for production
import json # For loading the pre-generated JSON
from flask import Blueprint, jsonify, render_template_string, current_app, render_template, send_from_directory
from werkzeug.exceptions import HTTPException

from OpenMediaMatch.utils.flask_utils import api_error_handler

bp = Blueprint("openapi", __name__)
bp.register_error_handler(HTTPException, api_error_handler)

# Directory where openapi.json and openapi.yaml are stored
# Adjust the path depth according to the new file location if it changes.
# Assuming openapi.json and openapi.yaml are in the root of the 'hasher-matcher-actioner' directory
OPENAPI_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "openapi_files" # Let's assume we'll place them in a dedicated folder
)
# Create this directory if it doesn't exist, or ensure files are placed here.
# For now, let's assume the files will be directly in the project root for simplicity,
# matching the 'openapi.yaml' location.
# Revised path to project root where openapi.yaml and eventually openapi.json will reside.
SPEC_FILES_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), # current blueprint's directory
    "..", # up to src/OpenMediaMatch
    "..", # up to src
    "..", # up to hasher-matcher-actioner (project root)
))


@bp.route("/openapi.json")
def openapi_json():
    """
    Serve the pre-generated OpenAPI specification as JSON.
    """
    try:
        # Path to the pre-generated openapi.json file
        # Ensure 'openapi.json' is in the root of 'hasher-matcher-actioner'
        return send_from_directory(SPEC_FILES_DIR, "openapi.json", mimetype='application/json')
    except FileNotFoundError:
        current_app.logger.error(f"openapi.json not found in {SPEC_FILES_DIR}")
        return jsonify({"error": "OpenAPI JSON specification not found"}), 500

@bp.route("/openapi.yaml")
def openapi_yaml():
    """
    Serve the pre-generated OpenAPI specification as YAML.
    """
    try:
        # Path to the openapi.yaml file
        # Ensure 'openapi.yaml' is in the root of 'hasher-matcher-actioner'
        return send_from_directory(SPEC_FILES_DIR, "openapi.yaml", mimetype='text/yaml')
    except FileNotFoundError:
        current_app.logger.error(f"openapi.yaml not found in {SPEC_FILES_DIR}")
        return jsonify({"error": "OpenAPI YAML specification not found"}), 500

@bp.route("/docs")
def swagger_ui():
    """
    Serve Swagger UI for interactive API documentation.
    """
    # This HTML can remain as is, or be moved to a template if preferred.
    # It correctly points to /api/openapi.json
    swagger_ui_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>HMA API Documentation - Swagger UI</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.10.5/swagger-ui.css" />
    <style>
        html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
        *, *:before, *:after { box-sizing: inherit; }
        body { margin:0; background: #fafafa; }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.10.5/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.10.5/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: "/api/openapi.json", // Points to our static JSON
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [ SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset ],
                plugins: [ SwaggerUIBundle.plugins.DownloadUrl ],
                layout: "StandaloneLayout",
                validatorUrl: null, // Disable validation, spec is pre-validated
                docExpansion: "list",
                filter: true,
                showRequestHeaders: true,
                showCommonExtensions: true,
                tryItOutEnabled: true, // Enable "Try it out" feature
            });
        };
    </script>
</body>
</html>
    '''
    return render_template_string(swagger_ui_html)

@bp.route("/redoc")
def redoc():
    """
    Serve ReDoc for alternative API documentation.
    """
    # This HTML can remain as is, or be moved to a template if preferred.
    # It correctly points to /api/openapi.json
    redoc_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>HMA API Documentation - ReDoc</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    <style> body { margin: 0; padding: 0; } </style>
</head>
<body>
    <redoc spec-url='/api/openapi.json'></redoc> {/* Points to our static JSON */}
    <script src="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js"></script>
</body>
</html>
    '''
    return render_template_string(redoc_html)

@bp.route("/")
def api_home():
    """
    API documentation home page.
    This provides links to different documentation formats and tools.
    """
    # This should still work as api_home.html uses relative /api/... links
    return render_template("api_home.html") 