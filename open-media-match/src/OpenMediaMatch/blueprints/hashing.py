# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Endpoints for hashing content
"""

from pathlib import Path
import tempfile
import typing as t

from flask import Blueprint
from flask import abort, request, current_app
import requests

from threatexchange.content_type.content_base import ContentType
from threatexchange.content_type.photo import PhotoContent
from threatexchange.content_type.video import VideoContent
from threatexchange.signal_type.signal_base import FileHasher, SignalType

from OpenMediaMatch.persistence import get_storage
from OpenMediaMatch.utils import abort_to_json

bp = Blueprint("hashing", __name__)


@bp.route("/hash")
@abort_to_json
def hash_media():
    """
    Fetch content and return its hash.
    """
    media_url = request.args.get("url", None)
    if media_url is None:
        return {"message": "url is required"}, 400

    download_resp = requests.get(media_url, allow_redirects=True, timeout=30 * 1000)
    download_resp.raise_for_status()

    url_content_type = download_resp.headers["content-type"]

    current_app.logger.debug("%s is type %s", media_url, url_content_type)

    content_type = _parse_request_content_type(url_content_type)
    signal_types = _parse_request_signal_type(content_type)

    ret = {}

    # For images, we may need to copy the file suffix (.png, jpeg, etc) for it to work
    with tempfile.NamedTemporaryFile("wb") as tmp:
        current_app.logger.debug("Writing to %s", tmp.name)
        tmp.write(download_resp.content)
        path = Path(tmp.name)
        for st in signal_types.values():
            # At this point, every BytesHasher is a FileHasher, but we could
            # explicitly pull those out to avoiding storing any copies of
            # data locally, even temporarily
            if issubclass(st, FileHasher):
                ret[st.get_name()] = st.hash_from_file(path)
    return ret


def _parse_request_content_type(url_content_type: str) -> t.Type[ContentType]:
    arg = request.args.get("content_type", "")
    if not arg:
        if url_content_type.lower().startswith("image"):
            arg = PhotoContent.get_name()
        elif url_content_type.lower().startswith("video"):
            arg = VideoContent.get_name()
        else:
            abort(
                400,
                f"unsupported url ContentType: '{url_content_type}', "
                "if you know the expected type, provide it with content_type",
            )

    content_type_config = get_storage().get_content_type_configs().get(arg)
    if content_type_config is None:
        abort(400, f"no such content_type: '{arg}'")

    if not content_type_config.enabled:
        abort(400, f"content_type {arg} is disabled")

    return content_type_config.content_type


def _parse_request_signal_type(
    content_type: t.Type[ContentType],
) -> t.Mapping[str, t.Type[SignalType]]:
    signal_types = get_storage().get_enabled_signal_types_for_content_type(content_type)
    if not signal_types:
        abort(500, "No signal types configured!")
    signal_type_args = request.args.get("types", None)
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
