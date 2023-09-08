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
from threatexchange.signal_type.signal_base import FileHasher, SignalType

from OpenMediaMatch import app_resources

bp = Blueprint("hashing", __name__)


@bp.route("/hash")
def hash_media():
    """
    Fetch content and return its hash.
    TODO: implement
    """

    content_type = _parse_request_content_type()
    signal_types = _parse_request_signal_type(content_type)

    media_url = request.args.get("url", None)
    if media_url is None:
        current_app.logger.error("url is required")
        abort(400)

    download_resp = requests.get(media_url, allow_redirects=True, timeout=30 * 1000)
    download_resp.raise_for_status()

    ret = {}

    # TODO: For images, we have to copy the suffix for it to process propery
    with tempfile.NamedTemporaryFile("wb") as tmp:
        current_app.logger.debug("Writing to %s", tmp.name)
        tmp.write(download_resp.content)
        path = Path(tmp.name)
        for st in signal_types.values():
            if st is FileHasher:
                ret[st.get_name()] = st.hash_from_file(path)
    return ret


def _parse_request_content_type() -> ContentType:
    storage = app_resources.get_storage()
    arg = request.args.get("content_type", None)
    content_type_config = storage.get_content_type_configs().get(arg)
    if content_type_config is None:
        current_app.logger.error("no such content type: '%s'", arg)
        abort(400)

    if not content_type_config.enabled:
        current_app.logger.error("content type %s is disabled", arg)
        abort(400)

    return content_type_config.content_type


def _parse_request_signal_type(content_type: ContentType) -> t.Mapping[str, SignalType]:
    storage = app_resources.get_storage()
    signal_types = storage.get_enabled_signal_types_for_content_type(content_type)
    if not signal_types:
        current_app.logger.critical("No signal types configured!")
        abort(500)
    signal_type_args = request.args.get("types", None)
    if signal_type_args is None:
        return signal_types

    ret = {}
    for st_name in signal_type_args.split(","):
        st_name = st_name.trim()
        if not st_name:
            continue
        if st_name not in signal_types:
            current_app.logger.error("signal type '%s' doesn't exist or is disabled")
            abort(400)
        ret[st_name] = signal_types[st_name]

    if not ret:
        current_app.logger.error("empty signal type selection")
        abort(400)

    return ret
