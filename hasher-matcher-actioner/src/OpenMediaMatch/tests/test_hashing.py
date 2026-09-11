# Copyright (c) Meta Platforms, Inc. and affiliates.

import io
import sys
import tempfile
from pathlib import Path

import pytest
from unittest.mock import Mock, patch
from PIL import Image

from OpenMediaMatch.blueprints.hashing import DEFAULT_MAX_REMOTE_FILE_SIZE, is_valid_url
from OpenMediaMatch.tests.utils import app, client
from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.content_type.photo import PhotoContent
from threatexchange.content_type.video import VideoContent


def test_valid_urls(app):
    """Test various valid URLs that should pass validation."""
    valid_urls = [
        "https://example.com",
        "https://example.com/path",
        "https://example.com:8080/path",
        "http://example.com",
        "https://sub.example.com",
        "https://example.com/path?query=value",
        "https://example.com/path#fragment",
    ]

    with app.app_context():
        for url in valid_urls:
            assert is_valid_url(url), f"URL should be valid: {url}"


def test_invalid_schemes(app):
    """Test URLs with invalid schemes."""
    invalid_urls = [
        "ftp://example.com",
        "file:///etc/passwd",
        "javascript:alert(1)",
        "data:text/html,<script>alert(1)</script>",
        "ws://example.com",
        "wss://example.com",
    ]

    with app.app_context():
        for url in invalid_urls:
            assert not is_valid_url(url), f"URL should be invalid: {url}"


def test_missing_scheme_or_netloc(app):
    """Test URLs missing scheme or netloc."""
    invalid_urls = [
        "example.com",
        "//example.com",
        "http://",
        "https://",
        "",
        None,
    ]

    with app.app_context():
        for url in invalid_urls:
            assert not is_valid_url(url), f"URL should be invalid: {url}"


def test_malformed_urls(app):
    """Test malformed URLs."""
    invalid_urls = [
        "not a url",
        "http://",
        "https://",
        "http:///example.com",
        "http://example.com:",
        "http://example.com:abc",
    ]

    with app.app_context():
        for url in invalid_urls:
            assert not is_valid_url(url), f"URL should be invalid: {url}"


def test_allowed_hostnames(app):
    """Test hostname validation against allowed list."""
    with app.app_context():
        # Set test allowed hostnames
        app.config["ALLOWED_HOSTNAMES"] = {
            "example.com",
            "cdn.example.com",
            "media.example.com",
        }

        # Test allowed hostnames
        for hostname in app.config["ALLOWED_HOSTNAMES"]:
            url = f"https://{hostname}/path"
            assert is_valid_url(url), f"URL should be valid: {url}"

        # Test disallowed hostnames
        invalid_hostnames = [
            "https://evil.com",
            "https://malicious-site.com",
            "https://example.com.evil.com",  # Subdomain attack
            "https://evil.com/example.com",  # Path attack
        ]

        for url in invalid_hostnames:
            assert not is_valid_url(url), f"URL should be invalid: {url}"


def test_empty_allowed_hostnames(app):
    """Test behavior when ALLOWED_HOSTNAMES is empty."""
    with app.app_context():
        # Temporarily set empty allowed hostnames
        app.config["ALLOWED_HOSTNAMES"] = set()

        # All URLs should be allowed when ALLOWED_HOSTNAMES is empty
        test_urls = [
            "https://example.com",
            "https://evil.com",
            "https://any-domain.com",
        ]

        for url in test_urls:
            assert is_valid_url(
                url
            ), f"URL should be valid when ALLOWED_HOSTNAMES is empty: {url}"


@patch("requests.get")
def test_content_length_validation(mock_get, client):
    """Test content length validation."""
    # Mock GET response with large content length
    mock_get_resp = Mock()
    mock_get_resp.headers = {
        "content-type": "image/jpeg",
        "content-length": str(DEFAULT_MAX_REMOTE_FILE_SIZE + 1),
    }
    mock_get_resp.raise_for_status = Mock()
    mock_get.return_value = mock_get_resp

    # Test with large content length
    response = client.get("/h/hash?url=https://example.com/image.jpg")
    assert response.status_code == 413
    assert "Content too large" in response.get_data(as_text=True)

    # Mock GET response with acceptable content length
    mock_get_resp.headers = {
        "content-type": "image/jpeg",
        "content-length": str(DEFAULT_MAX_REMOTE_FILE_SIZE - 1),
    }
    mock_get_resp.iter_content.return_value = [b"fake image data"]

    # Test with acceptable content length
    response = client.get("/h/hash?url=https://example.com/image.jpg")
    assert response.status_code != 413


@patch("requests.get")
def test_content_length_validation_default(mock_get, client, app):
    with app.app_context():
        # Override MAX_REMOTE_FILE_SIZE to None, simulating it not
        # being present in an OMM_CONFIG file:
        app.config["MAX_REMOTE_FILE_SIZE"] = None

        # Mock GET response with large content length
        mock_get_resp = Mock()
        mock_get_resp.headers = {
            "content-type": "image/jpeg",
            "content-length": str(DEFAULT_MAX_REMOTE_FILE_SIZE + 1),
        }
        mock_get_resp.raise_for_status = Mock()
        mock_get.return_value = mock_get_resp

        # Test with large content length
        response = client.get("/h/hash?url=https://example.com/image.jpg")
        assert response.status_code == 413
        assert "Content too large" in response.get_data(as_text=True)


@patch("requests.get")
def test_content_length_validation_misconfiguration(mock_get, client, app):
    with app.app_context():
        # Override MAX_REMOTE_FILE_SIZE to a non-integer value, simulating it
        # being set from the environment variables incorrectly:
        app.config["MAX_REMOTE_FILE_SIZE"] = "not-an-integer"

        mock_get_resp = Mock()
        mock_get_resp.headers = {
            "content-type": "image/jpeg",
            "content-length": str(DEFAULT_MAX_REMOTE_FILE_SIZE + 1),
        }
        mock_get_resp.raise_for_status = Mock()
        mock_get.return_value = mock_get_resp

        # Test with large content length
        response = client.get("/h/hash?url=https://example.com/image.jpg")
        assert response.status_code == 500
        assert "Service misconfigured, see logs for details" in response.get_data(
            as_text=True
        )


# ---------------------------------------------------------------------------
# S3 fetching (s3://bucket/key)
# ---------------------------------------------------------------------------


def _checkerboard_jpeg_bytes(cell: int = 8) -> bytes:
    """Build a deterministic in-memory JPEG for hashing assertions."""
    img = Image.new("RGB", (128, 128))
    pixels = img.load()
    assert pixels is not None
    for x in range(128):
        for y in range(128):
            pixels[x, y] = (255, 255, 255) if (x // cell + y // cell) % 2 else (0, 0, 0)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _pdq_of(data: bytes) -> str:
    with tempfile.NamedTemporaryFile("wb", suffix=".jpg") as tmp:
        tmp.write(data)
        tmp.flush()
        return PdqSignal.hash_from_file(Path(tmp.name))


def _mock_s3_client(
    data: bytes,
    *,
    content_type: str = "image/jpeg",
    content_length: object = ...,  # sentinel: default to len(data), pass None to omit
) -> Mock:
    """Build a mock boto3 S3 client returning `data` for the requested object."""
    head: dict = {"ContentType": content_type}
    length = len(data) if content_length is ... else content_length
    if length is not None:
        head["ContentLength"] = length

    body = Mock()
    body.iter_chunks.return_value = [data]

    mock_client = Mock()
    mock_client.head_object.return_value = head
    mock_client.get_object.return_value = {"Body": body}
    return mock_client


@patch("boto3.client")
def test_s3_hash_happy_path(mock_boto_client, client):
    data = _checkerboard_jpeg_bytes()
    mock_boto_client.return_value = _mock_s3_client(data)

    response = client.get("/h/hash?url=s3://my-bucket/path/to/image.jpg")

    assert response.status_code == 200, response.get_data(as_text=True)
    assert response.json == {"pdq": _pdq_of(data)}

    # Bucket/key were parsed correctly and passed through to boto3.
    mock_boto_client.return_value.head_object.assert_called_once_with(
        Bucket="my-bucket", Key="path/to/image.jpg"
    )
    mock_boto_client.return_value.get_object.assert_called_once_with(
        Bucket="my-bucket", Key="path/to/image.jpg"
    )


@patch("boto3.client")
def test_s3_endpoint_and_region_config(mock_boto_client, client, app):
    with app.app_context():
        app.config["S3_ENDPOINT_URL"] = "https://minio.example.com"
        app.config["S3_REGION_NAME"] = "us-east-1"
        data = _checkerboard_jpeg_bytes()
        mock_boto_client.return_value = _mock_s3_client(data)

        response = client.get("/h/hash?url=s3://my-bucket/image.jpg")
        assert response.status_code == 200

        mock_boto_client.assert_called_once_with(
            "s3",
            endpoint_url="https://minio.example.com",
            region_name="us-east-1",
        )


@pytest.mark.parametrize("url", ["s3://my-bucket", "s3://", "s3:///key-no-bucket"])
def test_s3_invalid_url(client, url):
    response = client.get(f"/h/hash?url={url}")
    assert response.status_code == 400
    assert "Invalid S3 URL" in response.get_data(as_text=True)


def test_s3_bucket_not_in_allowlist(client, app):
    with app.app_context():
        app.config["ALLOWED_S3_BUCKETS"] = {"allowed-bucket"}
        response = client.get("/h/hash?url=s3://other-bucket/image.jpg")
        assert response.status_code == 400
        assert "not in the allowed list" in response.get_data(as_text=True)


@patch("boto3.client")
def test_s3_bucket_in_allowlist(mock_boto_client, client, app):
    with app.app_context():
        app.config["ALLOWED_S3_BUCKETS"] = {"allowed-bucket"}
        data = _checkerboard_jpeg_bytes()
        mock_boto_client.return_value = _mock_s3_client(data)

        response = client.get("/h/hash?url=s3://allowed-bucket/image.jpg")
        assert response.status_code == 200


@patch("boto3.client")
def test_s3_content_too_large_by_content_length(mock_boto_client, client, app):
    with app.app_context():
        app.config["MAX_REMOTE_FILE_SIZE"] = 10
        data = _checkerboard_jpeg_bytes()
        mock_boto_client.return_value = _mock_s3_client(data)  # ContentLength >> 10

        response = client.get("/h/hash?url=s3://my-bucket/image.jpg")
        assert response.status_code == 413
        assert "Content too large" in response.get_data(as_text=True)


@patch("boto3.client")
def test_s3_content_too_large_while_streaming(mock_boto_client, client, app):
    """ContentLength absent (or wrong) - the streaming cap must still trip."""
    with app.app_context():
        app.config["MAX_REMOTE_FILE_SIZE"] = 10
        data = _checkerboard_jpeg_bytes()
        # Omit ContentLength so the only defense is the streaming byte counter.
        mock_boto_client.return_value = _mock_s3_client(data, content_length=None)

        response = client.get("/h/hash?url=s3://my-bucket/image.jpg")
        assert response.status_code == 413
        assert "Content too large" in response.get_data(as_text=True)


@patch("boto3.client")
def test_s3_object_not_found(mock_boto_client, client):
    from botocore.exceptions import ClientError

    mock_client = Mock()
    mock_client.head_object.side_effect = ClientError(
        {
            "Error": {"Code": "404", "Message": "Not Found"},
            "ResponseMetadata": {"HTTPStatusCode": 404},
        },
        "HeadObject",
    )
    mock_boto_client.return_value = mock_client

    response = client.get("/h/hash?url=s3://my-bucket/missing.jpg")
    assert response.status_code == 404
    assert "Could not access" in response.get_data(as_text=True)


def test_s3_boto3_not_installed(client):
    # Simulate boto3 being absent: importing it raises ImportError.
    with patch.dict(sys.modules, {"boto3": None}):
        response = client.get("/h/hash?url=s3://my-bucket/image.jpg")
    assert response.status_code == 500
    assert "requires the 'boto3' package" in response.get_data(as_text=True)
