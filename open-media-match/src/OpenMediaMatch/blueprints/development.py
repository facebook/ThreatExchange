# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Development only routes for easily testing functionality end-to-end, all running on a single host.
"""

from functools import reduce
import itertools
from flask import Blueprint, abort, redirect, request, url_for

from OpenMediaMatch.blueprints.hashing import hash_media
from OpenMediaMatch.blueprints.matching import lookup, lookup_signal
from OpenMediaMatch.utils import abort_to_json, require_request_param


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
                f"Requested signal type '{signal_type_name}' is not supported for the provided media.",
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
