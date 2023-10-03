# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Endpoints for matching content and hashes.
"""

from flask import Blueprint
from flask import abort
from threatexchange.signal_type.signal_base import SignalType
from OpenMediaMatch.storage.interface import IUnifiedStore

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
    return lookup_signal(signal, signal_type_name)


def lookup_signal(signal: str, signal_type_name: str) -> dict[str, list[int]]:
    storage = get_storage()
    signal_type = _validate_and_transform_signal_type(signal_type_name, storage)

    try:
        signal = signal_type.validate_signal_str(signal)
    except Exception as e:
        abort(400, f"invalid signal type: {e}")

    index = storage.get_signal_type_index(signal_type)
    if not index:
        abort(503, "index not yet ready")
    return {"matches": [m.metadata for m in index.query(signal)]}


def _validate_and_transform_signal_type(
    signal_type_name: str, storage: IUnifiedStore
) -> type[SignalType]:
    """
    Accepts a signal type name and returns the corresponding signal type class,
    validating that the signal type exists and is enabled for the provided storage.
    """
    signal_type_config = storage.get_signal_type_configs().get(signal_type_name)
    if signal_type_config is None:
        abort(400, f"No such SignalType '{signal_type_name}'")
    if not signal_type_config.enabled:
        abort(400, f"SignalType '{signal_type_name}' is not enabled")
    return signal_type_config.signal_type


@bp.route("/index/status")
def index_status():
    """
    Input:
     * Signal type (hash type)
    Output:
     * Time of last index build
    """
    abort(501)  # Unimplemented
