import pytest
from flask import url_for
import json # For test_openapi_json_endpoint

# TODO: Consider adding a more specific test for openapi.yaml content type if possible
# The dynamic server URL update is no longer part of openapi.py, so that TODO can be removed or re-evaluated
# if such a feature is added back via a different mechanism.

def test_openapi_json_endpoint(client):
    """Test that the /api/openapi.json endpoint returns a valid JSON response."""
    response = client.get(url_for('openapi.openapi_json'))
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    try:
        json_data = json.loads(response.data.decode('utf-8'))
    except json.JSONDecodeError as e:
        pytest.fail(f"Failed to parse JSON response: {e}")
    
    assert 'openapi' in json_data
    assert json_data['openapi'] == '3.0.0' # Check for OpenAPI version
    assert 'info' in json_data
    assert 'paths' in json_data
    assert 'components' in json_data

def test_openapi_yaml_endpoint(client):
    """Test that the /api/openapi.yaml endpoint returns a valid YAML response."""
    response = client.get(url_for('openapi.openapi_yaml'))
    assert response.status_code == 200
    assert response.content_type.startswith('text/yaml') 
    # Instead of parsing, check for a known YAML starting string
    response_text = response.data.decode('utf-8')
    assert response_text.startswith('openapi: 3.0.0')
    # Optionally, check for a few other key elements if needed, as plain text
    assert 'info:' in response_text
    assert 'paths:' in response_text
    assert 'components:' in response_text

def test_swagger_ui_endpoint(client):
    """Test that the /api/docs endpoint returns HTML for Swagger UI."""
    response = client.get(url_for('openapi.swagger_ui'))
    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'
    # Updated title check
    assert b'<title>HMA API Documentation - Swagger UI</title>' in response.data
    assert b'id="swagger-ui"' in response.data 
    assert b'url: "/api/openapi.json"' in response.data # Check it points to the JSON spec

def test_redoc_endpoint(client):
    """Test that the /api/redoc endpoint returns HTML for ReDoc."""
    response = client.get(url_for('openapi.redoc'))
    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'
    # Updated title check
    assert b'<title>HMA API Documentation - ReDoc</title>' in response.data
    assert b'<redoc spec-url=\'/api/openapi.json\'></redoc>' in response.data

def test_api_home_endpoint(client):
    """Test that the /api/ endpoint returns the API home page HTML."""
    response = client.get(url_for('openapi.api_home'))
    assert response.status_code == 200
    assert response.content_type == 'text/html; charset=utf-8'
    # Assuming api_home.html title is "HMA API Documentation" from previous setup
    # If api_home.html's title was also changed, this assert should be updated.
    # For now, assuming it refers to the general documentation page.
    assert b'<title>HMA API Documentation</title>' in response.data # Check title from api_home.html
    assert b'<h1>HMA API Documentation</h1>' in response.data
    assert b'href="/api/docs"' in response.data 
    assert b'href="/api/redoc"' in response.data 
    assert b'href="/api/openapi.json"' in response.data
    assert b'href="/api/openapi.yaml"' in response.data

# The fixture for get_openapi_spec is no longer relevant as the function was removed.
# Tests relying on direct spec object inspection would need to be re-thought
# if detailed validation of the static file content is needed beyond basic checks.
# For example, loading the openapi.json file directly in a test and validating its structure. 