# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Development only routes for easily testing functionality end-to-end, all running on a single host.
"""

import itertools
from flask import Blueprint, abort, request

from OpenMediaMatch.persistence import get_storage
from OpenMediaMatch.background_tasks import build_index
from OpenMediaMatch.blueprints.hashing import hash_media
from OpenMediaMatch.blueprints.matching import lookup_signal
from OpenMediaMatch.utils import abort_to_json


bp = Blueprint("development", __name__)


@bp.route("/query")
@abort_to_json
def query_media():
    """
    Hash the input media and then match against all banked content.
    This is simply a wrapper around the hasing and matching APIs.

     Input:
     * url - path to the media to hash. Supports image or video.
     * signal_type - Signal type (hash type)

     Output:
        * List of matching content items
    """
    signal_type_to_signal_map = hash_media()
    if not isinstance(signal_type_to_signal_map, dict):
        # We really should not get here, since if something went wrong, it should
        if isinstance(signal_type_to_signal_map, tuple):
            return signal_type_to_signal_map
        abort(500, "Something went wrong while hashing the provided media.")

    # Check if signal_type is an option in the map of hashes
    signal_type_name = request.args.get("signal_type")
    if signal_type_name is not None:
        if signal_type_name not in signal_type_to_signal_map:
            abort(
                400,
                f"Requested signal type '{signal_type_name}' is not supported for the provided "
                "media.",
            )
        return lookup_signal(
            signal_type_to_signal_map[signal_type_name], signal_type_name
        )
    return {
        "matches": list(
            itertools.chain(
                *map(
                    lambda x: lookup_signal(x[1], x[0])["matches"],
                    signal_type_to_signal_map.items(),
                ),
            )
        )
    }


@bp.route("/rebuild_index", methods=["POST"])
@abort_to_json
def rebuild_index():
    data = request.json
    storage = get_storage()
    if "signal_type" in data:
        st_name = data["signal_type"]
        st = storage.get_signal_type_configs().get(st_name)
        if st is None:
            abort(404, f"No such signal type '{st_name}'")
        if not st.enabled:
            abort(400, f"Signal type {st_name} is disabled")
        build_index.build_index(st.signal_type)
        return {}
    build_index.build_all_indices(storage, storage, storage)
