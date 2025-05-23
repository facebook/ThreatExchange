# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
OpenAPI specification and documentation endpoints for HMA.
"""

import os
import yaml
from flask import Blueprint, jsonify, render_template_string, current_app
from werkzeug.exceptions import HTTPException

from OpenMediaMatch.utils.flask_utils import api_error_handler

bp = Blueprint("openapi", __name__)
bp.register_error_handler(HTTPException, api_error_handler)


def get_openapi_spec():
    """
    Load and return the OpenAPI specification.
    
    This function loads the openapi.yaml file and returns it as a dictionary.
    It also dynamically updates the server URLs based on the current request.
    """
    # Get the path to the openapi.yaml file
    openapi_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
        "..", "..", "openapi.yaml"
    )
    
    try:
        with open(openapi_path, 'r') as f:
            spec = yaml.safe_load(f)
        
        # Update server URLs dynamically if needed
        if hasattr(current_app, 'config') and current_app.config.get('SERVER_NAME'):
            server_name = current_app.config['SERVER_NAME']
            scheme = 'https' if current_app.config.get('PREFERRED_URL_SCHEME') == 'https' else 'http'
            spec['servers'] = [
                {
                    'url': f'{scheme}://{server_name}',
                    'description': 'Current server'
                }
            ]
        
        return spec
    except FileNotFoundError:
        current_app.logger.error(f"OpenAPI spec file not found at {openapi_path}")
        return None
    except yaml.YAMLError as e:
        current_app.logger.error(f"Error parsing OpenAPI spec: {e}")
        return None


@bp.route("/openapi.json")
def openapi_json():
    """
    Serve the OpenAPI specification as JSON.
    
    This endpoint returns the complete OpenAPI 3.0 specification for the HMA API
    in JSON format, which can be consumed by various OpenAPI tools.
    """
    spec = get_openapi_spec()
    if spec is None:
        return jsonify({"error": "OpenAPI specification not available"}), 500
    
    return jsonify(spec)


@bp.route("/openapi.yaml")
def openapi_yaml():
    """
    Serve the OpenAPI specification as YAML.
    
    This endpoint returns the complete OpenAPI 3.0 specification for the HMA API
    in YAML format.
    """
    spec = get_openapi_spec()
    if spec is None:
        return "error: OpenAPI specification not available", 500
    
    return yaml.dump(spec, default_flow_style=False), 200, {'Content-Type': 'text/yaml'}


@bp.route("/docs")
def swagger_ui():
    """
    Serve Swagger UI for interactive API documentation.
    
    This endpoint provides a web-based interface for exploring and testing
    the HMA API endpoints using Swagger UI.
    """
    swagger_ui_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>HMA API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.10.5/swagger-ui.css" />
    <style>
        html {
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }
        *, *:before, *:after {
            box-sizing: inherit;
        }
        body {
            margin:0;
            background: #fafafa;
        }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.10.5/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.10.5/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: '/api/openapi.json',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                validatorUrl: null,
                docExpansion: "list",
                filter: true,
                showRequestHeaders: true,
                showCommonExtensions: true,
                tryItOutEnabled: true,
                requestInterceptor: function(req) {
                    // Add any request interceptors here if needed
                    return req;
                },
                responseInterceptor: function(res) {
                    // Add any response interceptors here if needed  
                    return res;
                }
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
    
    This endpoint provides an alternative web-based interface for viewing
    the HMA API documentation using ReDoc.
    """
    redoc_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>HMA API Documentation</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    <style>
        body {
            margin: 0;
            padding: 0;
        }
    </style>
</head>
<body>
    <redoc spec-url='/api/openapi.json'></redoc>
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
    home_html = '''
<!DOCTYPE html>
<html>
<head>
    <title>HMA API Documentation</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            background: #f8f9fa;
        }
        .container {
            background: white;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #1976d2;
            border-bottom: 3px solid #1976d2;
            padding-bottom: 0.5rem;
        }
        h2 {
            color: #424242;
            margin-top: 2rem;
        }
        .links {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }
        .link-card {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 1.5rem;
            text-decoration: none;
            color: inherit;
            transition: all 0.3s ease;
        }
        .link-card:hover {
            border-color: #1976d2;
            box-shadow: 0 4px 15px rgba(25, 118, 210, 0.2);
        }
        .link-card h3 {
            margin: 0 0 0.5rem 0;
            color: #1976d2;
        }
        .link-card p {
            margin: 0;
            color: #666;
            font-size: 0.9rem;
        }
        .info-box {
            background: #e3f2fd;
            border-left: 4px solid #1976d2;
            padding: 1rem;
            margin: 1rem 0;
        }
        .role-info {
            background: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 1rem;
            margin: 1rem 0;
        }
        code {
            background: #f5f5f5;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 Hasher-Matcher-Actioner (HMA) API</h1>
        
        <div class="info-box">
            <strong>HMA</strong> is Meta's content moderation platform that provides content hashing, 
            similarity matching, and curation capabilities for trust & safety applications.
        </div>

        <h2>📚 API Documentation</h2>
        <div class="links">
            <a href="/api/docs" class="link-card">
                <h3>📖 Swagger UI</h3>
                <p>Interactive API documentation with try-it-out functionality</p>
            </a>
            
            <a href="/api/redoc" class="link-card">
                <h3>📄 ReDoc</h3>
                <p>Clean, responsive API documentation viewer</p>
            </a>
            
            <a href="/api/openapi.json" class="link-card">
                <h3>📋 OpenAPI JSON</h3>
                <p>Machine-readable API specification in JSON format</p>
            </a>
            
            <a href="/api/openapi.yaml" class="link-card">
                <h3>📝 OpenAPI YAML</h3>
                <p>Human-readable API specification in YAML format</p>
            </a>
        </div>

        <h2>🛠️ API Endpoints</h2>
        <div class="role-info">
            <strong>Role Requirements:</strong> Different endpoints require specific roles to be enabled in your HMA configuration:
            <ul>
                <li><code>ROLE_HASHER</code> - Required for <code>/h/*</code> endpoints</li>
                <li><code>ROLE_MATCHER</code> - Required for <code>/m/*</code> endpoints</li>
                <li><code>ROLE_CURATOR</code> - Required for <code>/c/*</code> endpoints</li>
                <li><code>UI_ENABLED</code> - Required for <code>/ui/*</code> endpoints</li>
            </ul>
        </div>

        <h3>🔨 Key Endpoint Categories</h3>
        <ul>
            <li><strong>Hashing (<code>/h/*</code>)</strong> - Content hashing operations</li>
            <li><strong>Matching (<code>/m/*</code>)</strong> - Content matching and lookup</li>
            <li><strong>Curation (<code>/c/*</code>)</strong> - Bank and content management</li>
            <li><strong>Development (<code>/dev/*</code>)</strong> - Testing and development tools</li>
        </ul>

        <h2>🚀 Quick Start</h2>
        <div class="info-box">
            <p><strong>Health Check:</strong> <code>GET /status</code></p>
            <p><strong>Hash Content:</strong> <code>GET /h/hash?url=https://example.com/image.jpg</code></p>
            <p><strong>Match Content:</strong> <code>GET /m/lookup?url=https://example.com/image.jpg</code></p>
            <p><strong>List Banks:</strong> <code>GET /c/banks</code></p>
        </div>

        <h2>🔗 External Resources</h2>
        <div class="links">
            <a href="https://github.com/facebook/ThreatExchange" class="link-card">
                <h3>🏠 ThreatExchange GitHub</h3>
                <p>Main project repository and documentation</p>
            </a>
            
            <a href="https://developers.facebook.com/docs/threat-exchange" class="link-card">
                <h3>📖 ThreatExchange Docs</h3>
                <p>Official documentation and best practices</p>
            </a>
        </div>
    </div>
</body>
</html>
    '''
    
    return render_template_string(home_html) 