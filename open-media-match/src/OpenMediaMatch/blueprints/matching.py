# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Endpoints for matching content and hashes.
"""

from flask import Blueprint
from flask import abort

from OpenMediaMatch.utils import (
    abort_to_json,
    require_request_param,
)
from OpenMediaMatch.persistence import get_storage

bp = Blueprint("matching", __name__)


@bp.route("/lookup")
@abort_to_json
def lookup():
    """
    Look up a hash in the similarity index
    Input:
     * Signal type (hash type)
     * Signal value (the hash)
     * Optional list of banks to restrict search to
    Output:
     * List of matching content items
    """
    signal = require_request_param("signal")
    signal_type_name = require_request_param("signal_type")
    storage = get_storage()
    signal_type_config = storage.get_signal_type_configs().get(signal_type_name)
    if signal_type_config is None:
        abort(f"No such SignalType '{signal_type_name}'", 400)
    if not signal_type_config.enabled:
        return {}  # Should this be an error?
    signal_type = signal_type_config.signal_type

    try:
        signal = signal_type.validate_signal_str(signal)
    except Exception as e:
        abort(400, f"invalid signal type: {e}")

    index = storage.get_signal_type_index(signal_type)
    if not index:
        abort(503, "index not yet ready")
    return {"matches": [m.metadata for m in index.query(signal)]}


@bp.route("/index/status")
def index_status():
    """
    Input:
     * Signal type (hash type)
    Output:
     * Time of last index build
    """
    abort(501)  # Unimplemented
