# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Endpoints for matching content and hashes.
"""

import random

from flask import Blueprint
from flask import abort, current_app, request
from werkzeug.exceptions import HTTPException

from threatexchange.signal_type.signal_base import SignalType

from OpenMediaMatch.storage.interface import ISignalTypeConfigStore
from OpenMediaMatch.blueprints import hashing
from OpenMediaMatch.utils.flask_utils import require_request_param, api_error_handler
from OpenMediaMatch.persistence import get_storage

bp = Blueprint("matching", __name__)
bp.register_error_handler(HTTPException, api_error_handler)


@bp.route("/raw_lookup")
def raw_lookup():
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

    current_app.logger.debug("[lookup_signal] loading index")
    index = storage.get_signal_type_index(signal_type)

    if not index:
        abort(503, "index not yet ready")
    current_app.logger.debug("[lookup_signal] querying index")
    results = index.query(signal)
    current_app.logger.debug("[lookup_signal] query complete")
    return {"matches": [m.metadata for m in results]}


def _validate_and_transform_signal_type(
    signal_type_name: str, storage: ISignalTypeConfigStore
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


@bp.route("/lookup", methods=["GET"])
def lookup_get():
    """
    Look up a hash in the similarity index. The hash can either be specified via
    `signal_type` and `signal` query params, or a file url can be provided in the
    `url` query param.
    Input:
     Either:
     * File URL (`url`)
     * Optional content type (`content_type`)
     Or:
     * Signal type (hash type)
     * Signal value (the hash)

     Also (applies to both cases):
     * Optional seed (content id) for consistent coinflip
    Output:
     * List of matching banks
    """
    # Url was passed as a query param?
    if request.args.get("url", None):
        hashes = hashing.hash_media()
        resp = {}
        for signal_type in hashes.keys():
            signal = hashes[signal_type]
            resp[signal_type] = lookup(signal, signal_type)
    else:
        signal = require_request_param("signal")
        signal_type = require_request_param("signal_type")
        resp = lookup(signal, signal_type)

    return resp


@bp.route("/lookup", methods=["POST"])
def lookup_post():
    """
    Look up the hash for the uploaded file in the similarity index.
    @see OpenMediaMatch.blueprints.hashing hash_media_post()

    Input:
     * Uploaded file.
     * Optional seed (content id) for consistent coinflip
    Output:
     * List of matching banks
    """
    hashes = hashing.hash_media_post()

    resp = {}
    for signal_type in hashes.keys():
        signal = hashes[signal_type]
        resp[signal_type] = lookup(signal, signal_type)

    return resp


def lookup(signal, signal_type_name):
    current_app.logger.debug("performing lookup")
    raw_results = lookup_signal(signal, signal_type_name)
    storage = get_storage()
    current_app.logger.debug("getting bank content")
    contents = storage.bank_content_get(
        {cid for l in raw_results.values() for cid in l}
    )
    enabled = [c for c in contents if c.enabled]
    current_app.logger.debug(
        "lookup matches %d content ids (%d enabled)", len(contents), len(enabled)
    )
    if not enabled:
        return []
    banks = {c.bank.name: c.bank for c in enabled}
    rand = random.Random(request.args.get("seed"))
    coinflip = rand.random()
    enabled_banks = [
        b.name for b in banks.values() if b.matching_enabled_ratio >= coinflip
    ]
    current_app.logger.debug(
        "lookup matches %d banks (%d enabled)", len(banks), len(enabled_banks)
    )
    return enabled_banks


@bp.route("/index/status")
def index_status():
    """
    Get the status of matching indices.

    You can limit to just a single type with the signal_type parameter.

    Example Output:
    {
        "pdq": {
            "built_to": -1,
            "present": false,
            "size": 0
        },
        "video_md5": {
            "built_to": 1700146048,
            "present": true,
            "size": 591
        }
    }
    """
    storage = get_storage()
    signal_types = storage.get_signal_type_configs()

    limit_to_type = request.args.get("signal_type")
    if limit_to_type is not None:
        if limit_to_type not in signal_types:
            abort(400, f"No such signal type '{limit_to_type}'")
        signal_types = {limit_to_type: signal_types[limit_to_type]}

    status_by_name = {}
    for name, st in signal_types.items():
        checkpoint = storage.get_last_index_build_checkpoint(st.signal_type)

        status = {
            "present": False,
            "built_to": -1,
            "size": 0,
        }
        if checkpoint is not None:
            status = {
                "present": True,
                "built_to": checkpoint.last_item_timestamp,
                "size": checkpoint.total_hash_count,
            }
        status_by_name[name] = status
    return status_by_name
