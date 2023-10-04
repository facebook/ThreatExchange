# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Endpoints for matching content and hashes.
"""

import random

from flask import Blueprint
from flask import abort, current_app, request
from threatexchange.signal_type.signal_base import SignalType
from OpenMediaMatch.storage.interface import ISignalTypeConfigStore
from OpenMediaMatch.blueprints import hashing

from OpenMediaMatch.utils import (
    abort_to_json,
    require_request_param,
)
from OpenMediaMatch.persistence import get_storage

bp = Blueprint("matching", __name__)


@bp.route("/raw_lookup")
@abort_to_json
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

    index = storage.get_signal_type_index(signal_type)
    if not index:
        abort(503, "index not yet ready")
    return {"matches": [m.metadata for m in index.query(signal)]}


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
@abort_to_json
def lookup_get():
    """
    Look up a hash in the similarity index. The hash can either be specified via
    `signal_type` and `signal` query params, or a file url can be provided in the
    `url` query param.
    Input:
     * Signal type (hash type)
     * Signal value (the hash)
     * Optional seed (content id) for consistent coinflip
    Output:
     * List of matching banks
    """
    # Url was passed as a query param?
    if request.args.get("url", None):
        hash = hashing.hash_media()
        # The hash_media function returns an object with a single key
        # (the signal_type) and value (the signal)
        signal_type = list(hash.keys())[0]
        signal = hash[signal_type]
    else:
        signal = require_request_param("signal")
        signal_type = require_request_param("signal_type")

    return lookup(signal, signal_type)


@bp.route("/lookup", methods=["POST"])
@abort_to_json
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
    hash = hashing.hash_media_post()

    # The hash function returns an object with a single key (the signal_type) and value (the signal)
    signal_type = list(hash.keys())[0]
    signal = hash[signal_type]

    return lookup(signal, signal_type)


def lookup(signal, signal_type_name):
    raw_results = lookup_signal(signal, signal_type_name)
    storage = get_storage()
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
        "lookup matches %d banks (%d enabked)", len(banks), len(enabled_banks)
    )
    return enabled_banks


@bp.route("/index/status")
def index_status():
    """
    Input:
     * Signal type (hash type)
    Output:
     * Time of last index build
    """
    abort(501)  # Unimplemented
