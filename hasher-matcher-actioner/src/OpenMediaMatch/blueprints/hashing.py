# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Endpoints for hashing content
"""

from pathlib import Path
import tempfile
import typing as t
import requests
import logging
from urllib.parse import urlparse

from flask_openapi3 import APIBlueprint
from flask_openapi3.models import Tag
from flask import abort, request, current_app
from werkzeug.exceptions import HTTPException

from threatexchange.content_type.content_base import ContentType
from threatexchange.content_type.photo import PhotoContent
from threatexchange.content_type.video import VideoContent
from threatexchange.signal_type.signal_base import FileHasher, BytesHasher, SignalType

from OpenMediaMatch.persistence import get_storage
from OpenMediaMatch.utils import flask_utils
from OpenMediaMatch.schemas.hashing import HashRequest, HashResponse
from OpenMediaMatch.schemas.shared import ErrorResponse

logger = logging.getLogger(__name__)

bp = APIBlueprint("hashing", __name__, url_prefix="/h")
bp.register_error_handler(HTTPException, flask_utils.api_error_handler)

# Add these constants at the top level
DEFAULT_MAX_REMOTE_FILE_SIZE = 100 * 1024 * 1024  # 100MB max file size


def is_valid_url(url: str) -> bool:
    """
    Validate URL to prevent SSRF attacks.
    Returns True if URL is safe, False otherwise.
    """
    try:
        parsed = urlparse(url)

        if not parsed.scheme or not parsed.netloc:
            return False

        if parsed.scheme not in ("http", "https"):
            return False

        hostname = parsed.netloc.split(":")[0]
        # Check for malformed URLs with invalid port numbers
        if ":" in parsed.netloc and not parsed.netloc.split(":")[1].isdigit():
            return False

        # For testing, allow GitHub domains
        if hostname in ("github.com", "raw.githubusercontent.com"):
            return True

        # Check if there is an allowlist and hostname matches.
        allowed_hostnames = current_app.config.get("ALLOWED_HOSTNAMES", set())
        if not allowed_hostnames:
            return True

        if any(
            hostname == allowed or hostname.endswith(f".{allowed}")
            for allowed in allowed_hostnames
        ):
            return True

        return False
    except Exception as e:
        logger.warning(f"URL validation error: {str(e)}")
        return False


def _check_content_length_stream_response(
    url: str, max_length: int = DEFAULT_MAX_REMOTE_FILE_SIZE
) -> requests.Response:
    """
    Check for content length and raise an exception if it exceeds max_length.
    Returns the response as a stream.
    """
    response = requests.get(url, stream=True, timeout=30, allow_redirects=True)
    response.raise_for_status()

    content_length = response.headers.get("content-length")
    if content_length is not None and int(content_length) > max_length:
        abort(413, "Content too large")

    return response


def _resolve_max_remote_file_size() -> int:
    """
    Resolve the configured maximum remote file size, coercing string values
    (e.g. from environment variables) to an int.
    """
    max_file_size = (
        current_app.config.get("MAX_REMOTE_FILE_SIZE") or DEFAULT_MAX_REMOTE_FILE_SIZE
    )

    # cast to integer if necessary (the value could have come from an environment variable)
    if isinstance(max_file_size, str):
        if not max_file_size.isdigit():
            logger.error(
                f"MAX_REMOTE_FILE_SIZE misconfigured, expected integer, received: {max_file_size}"
            )
            abort(500, "Service misconfigured, see logs for details")
        max_file_size = int(max_file_size)

    return max_file_size


def _hash_chunks_to_signals(
    chunks: t.Iterable[bytes],
    signal_types: t.Mapping[str, t.Type[SignalType]],
    max_file_size: int,
) -> dict[str, str]:
    """
    Spool a byte stream to a temp file and hash it with each FileHasher signal
    type. The size cap is re-checked while streaming so a source that
    under-reports (or omits) its length still can't blow past the limit.

    Shared by the ``http(s)://`` and ``s3://`` fetch paths.
    """
    ret: dict[str, str] = {}
    # Some FileHashers care about the file suffix; a NamedTemporaryFile is close
    # enough in practice for the signal types HMA ships with.
    with tempfile.NamedTemporaryFile("wb") as tmp:
        current_app.logger.debug("Writing to %s", tmp.name)
        bytes_read = 0
        with tmp.file as temp_file:  # ensures bytes are flushed before we hash
            for chunk in chunks:
                if not chunk:
                    continue
                bytes_read += len(chunk)
                if bytes_read > max_file_size:
                    abort(413, "Content too large")
                temp_file.write(chunk)
        path = Path(tmp.name)
        for st in signal_types.values():
            if issubclass(st, FileHasher):
                ret[st.get_name()] = st.hash_from_file(path)
    return ret


def _resolve_signal_types(
    source_content_type: str,
    content_type_hint: t.Optional[str],
    signal_type_names: t.Optional[str],
) -> t.Mapping[str, t.Type[SignalType]]:
    """
    Turn the content type reported by the source (an HTTP header or S3 metadata),
    plus the optional caller overrides, into the set of signal types to hash.
    """
    content_type = _parse_request_content_type(
        source_content_type, override=content_type_hint
    )
    return _parse_request_signal_type(content_type, override=signal_type_names)


@bp.get(
    "/hash",
    tags=[Tag(name="Hashing")],
    responses={"200": HashResponse, "400": ErrorResponse, "413": ErrorResponse},
    summary="Hash content from URL",
    description=(
        "Fetch content from a URL and return its hash values for all supported "
        "signal types. Supports http(s):// URLs, and s3://bucket/key URLs when "
        "HMA is installed with the optional 's3' extra."
    ),
)
def hash_media(query: HashRequest) -> dict[str, str]:
    """
    Fetch content and return its hash.

    Input:
        * url - path to the media to hash. Supports image or video.
          Accepts http(s):// URLs and s3://bucket/key URLs.

    Output:
        * Mapping of signal types to hash values. Signal types are derived from the content type of the provided URL
    """
    try:
        result = hash_url_content(
            query.url,
            content_type_hint=query.content_type,
            signal_type_names=query.types,
        )
    except ValueError as e:
        abort(400, str(e))
    response = HashResponse(**result)
    return response.model_dump()


def hash_url_content(
    media_url: str,
    *,
    content_type_hint: t.Optional[str] = None,
    signal_type_names: t.Optional[str] = None,
) -> dict[str, str]:
    """
    Utility function to hash content from a URL.

    Supports ``http(s)://`` URLs as well as ``s3://bucket/key`` URLs when the
    optional boto3 dependency is installed (see :func:`hash_s3_content`).

    Args:
        media_url: URL to the media content
        content_type_hint: Optional content type name to avoid request arg lookup
        signal_type_names: Optional comma-separated signal types to hash

    Returns:
        Mapping of signal types to hash values

    Raises:
        ValueError: If URL is invalid or content cannot be hashed
    """
    if urlparse(media_url).scheme == "s3":
        return hash_s3_content(
            media_url,
            content_type_hint=content_type_hint,
            signal_type_names=signal_type_names,
        )

    if not is_valid_url(media_url):
        abort(400, "Invalid or unsafe URL provided")

    max_file_size = _resolve_max_remote_file_size()

    try:
        with _check_content_length_stream_response(
            media_url, max_file_size
        ) as download_resp:
            url_content_type = download_resp.headers["content-type"]
            current_app.logger.debug("%s is type %s", media_url, url_content_type)
            signal_types = _resolve_signal_types(
                url_content_type, content_type_hint, signal_type_names
            )
            return _hash_chunks_to_signals(
                download_resp.iter_content(chunk_size=8192),
                signal_types,
                max_file_size,
            )
    except requests.exceptions.RequestException as e:
        abort(400, f"Failed to fetch URL: {str(e)}")


def _s3_split_url(media_url: str) -> tuple[str, str]:
    """
    Split an ``s3://bucket/key`` URL into ``(bucket, key)``, aborting 400 if it
    is not well-formed. Also enforces the optional ``ALLOWED_S3_BUCKETS``
    allowlist (the S3 analogue of ``ALLOWED_HOSTNAMES``).
    """
    parsed = urlparse(media_url)
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")  # S3 keys are never rooted with "/"
    if parsed.scheme != "s3" or not bucket or not key:
        abort(400, "Invalid S3 URL, expected s3://bucket/key")

    allowed = current_app.config.get("ALLOWED_S3_BUCKETS")
    if allowed and bucket not in allowed:
        abort(400, f"S3 bucket '{bucket}' is not in the allowed list")

    return bucket, key


def _get_s3_client() -> t.Any:
    """
    Build a boto3 S3 client, aborting 500 if the optional ``boto3`` package is
    not installed.

    Credentials come from boto3's standard provider chain. ``S3_ENDPOINT_URL``
    points at an S3-compatible store (MinIO, DigitalOcean Spaces, ...) and
    ``S3_REGION_NAME`` sets the region.
    """
    try:
        import boto3
    except ImportError:
        abort(
            500,
            "S3 support requires the 'boto3' package. "
            "Install it with 'pip install OpenMediaMatch[s3]'.",
        )

    return boto3.client(
        "s3",
        endpoint_url=current_app.config.get("S3_ENDPOINT_URL") or None,
        region_name=current_app.config.get("S3_REGION_NAME") or None,
    )


def _s3_call(fn: t.Callable[..., t.Any], media_url: str, /, **kwargs: t.Any) -> t.Any:
    """
    Invoke a boto3 S3 client call, mapping botocore failures onto HTTP errors:
    403/404 pass through, other API errors are 400, transport failures are 502.
    Response bodies never echo the raw provider message.
    """
    from botocore.exceptions import BotoCoreError, ClientError

    try:
        return fn(**kwargs)
    except ClientError as e:
        status = int(e.response.get("ResponseMetadata", {}).get("HTTPStatusCode", 400))
        if status in (403, 404):
            abort(status, f"Could not access {media_url}")
        current_app.logger.warning("S3 error for %s: %s", media_url, e)
        abort(400, "Failed to fetch S3 object")
    except BotoCoreError as e:
        current_app.logger.error("S3 transport error for %s: %s", media_url, e)
        abort(502, "Failed to reach S3 storage")


def hash_s3_content(
    media_url: str,
    *,
    content_type_hint: t.Optional[str] = None,
    signal_type_names: t.Optional[str] = None,
) -> dict[str, str]:
    """
    Hash an object in S3-compatible storage, addressed by an ``s3://bucket/key``
    URL. Reached from :func:`hash_url_content` for ``s3://`` URLs.

    ``head_object`` supplies the content type and a size pre-check; the object
    is then streamed via ``get_object`` and hashed by
    :func:`_hash_chunks_to_signals`, which re-checks the size cap as it reads.
    """
    bucket, key = _s3_split_url(media_url)
    max_file_size = _resolve_max_remote_file_size()
    client = _get_s3_client()

    head = _s3_call(client.head_object, media_url, Bucket=bucket, Key=key)

    content_length = head.get("ContentLength")
    if content_length is not None and content_length > max_file_size:
        abort(413, "Content too large")

    # The stored content type may be a generic "binary/octet-stream" if none was
    # set at upload; the caller then has to pass content_type, as with http URLs.
    s3_content_type = head.get("ContentType", "")
    current_app.logger.debug("%s is type %s", media_url, s3_content_type)
    signal_types = _resolve_signal_types(
        s3_content_type, content_type_hint, signal_type_names
    )

    body = _s3_call(client.get_object, media_url, Bucket=bucket, Key=key)["Body"]
    return _hash_chunks_to_signals(
        body.iter_chunks(chunk_size=8192), signal_types, max_file_size
    )


@bp.post(
    "/hash",
    tags=[Tag(name="Hashing")],
    responses={"200": HashResponse, "400": ErrorResponse},
    summary="Hash uploaded file",
    description="Calculate hash for uploaded file via multipart/form-data",
)
def hash_media_post() -> dict[str, str]:
    """
    Calculate the hash for the provided file.
    """
    result = hash_media_from_form_data()
    response = HashResponse(**result)
    return response.model_dump()


def hash_media_from_form_data() -> dict[str, str]:
    """
    Hash the provided file and return the hash values.

    Input:
        * files - the multipart/form-data to hash (only one file allowed)

    Output:
        * Mapping of signal types to hash values
    """
    if not request.files:
        return abort(400, "Missing multipart/form-data file upload")

    # Let's just accept a single file per request. This keeps it consistent with the GET method.
    if len(request.files) > 1:
        abort(400, "Only one file allowed per request")

    ret = {}

    # Each file in a multipart/form-data body has a name as well as a filename:
    # Content-Disposition: form-data; name="field1"; filename="example.txt"
    # We will require that the field name is one of the supported content types.
    for field_name in request.files.keys():
        # The file key must be one of the supported content types.
        content_type = _lookup_content_type(field_name)
        signal_types = _parse_request_signal_type(content_type)

        if len(request.files.getlist(field_name)) > 1:
            abort(400, "Only one file allowed per request")

        for file in request.files.getlist(field_name):
            current_app.logger.debug(
                "Processing upload of type %s, filename=%s, mimetype=%s",
                field_name,
                file.filename,
                file.mimetype,
            )
            bytes = file.stream.read()
            for st in signal_types.values():
                if issubclass(st, BytesHasher):
                    ret[st.get_name()] = st.hash_from_bytes(bytes)

                elif issubclass(st, FileHasher):
                    with tempfile.NamedTemporaryFile("wb") as tmp:
                        current_app.logger.debug(
                            "Writing to %s for hashing, signal_type=%s",
                            tmp.name,
                            st.get_name(),
                        )
                        with tmp.file as temp_file:  # this ensures that bytes are flushed before hashing
                            temp_file.write(bytes)
                            path = Path(tmp.name)
                            ret[st.get_name()] = st.hash_from_file(path)

    return ret


def _parse_request_content_type(
    url_content_type: str, *, override: t.Optional[str] = None
) -> t.Type[ContentType]:
    arg = override or request.args.get("content_type", "")
    if not arg:
        if url_content_type.lower().startswith("image"):
            arg = PhotoContent.get_name()
        elif url_content_type.lower().startswith("video"):
            arg = VideoContent.get_name()
        else:
            abort(
                400,
                f"unsupported url ContentType: '{url_content_type}', "
                "if you know the expected type, provide it with the content_type query param",
            )
    return _lookup_content_type(arg)


def _lookup_content_type(arg: str) -> t.Type[ContentType]:
    content_type_config = get_storage().get_content_type_configs().get(arg)
    if content_type_config is None:
        abort(400, f"no such content_type: '{arg}'")

    if not content_type_config.enabled:
        abort(400, f"content_type {arg} is disabled")

    return content_type_config.content_type


def _parse_request_signal_type(
    content_type: t.Type[ContentType],
    *,
    override: t.Optional[str] = None,
) -> t.Mapping[str, t.Type[SignalType]]:
    """
    Parse the signal types from the request args.
    """
    signal_types = get_storage().get_enabled_signal_types_for_content_type(content_type)
    if not signal_types:
        abort(500, "No signal types configured!")
    signal_type_args = override if override is not None else request.args.get("types")
    if signal_type_args is None:
        return signal_types

    ret = {}
    for st_name in signal_type_args.split(","):
        st_name = st_name.strip()
        if not st_name:
            continue
        if st_name not in signal_types:
            abort(400, f"signal type '{st_name}' doesn't exist or is disabled")
        ret[st_name] = signal_types[st_name]

    if not ret:
        abort(400, "empty signal type selection")

    return ret
