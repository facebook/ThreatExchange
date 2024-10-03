# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Development only routes for easily testing functionality end-to-end, all running on a single host.
"""

import itertools
from flask import Blueprint, abort, request
from flask import redirect, url_for
from werkzeug.exceptions import HTTPException

from OpenMediaMatch.blueprints.hashing import hash_media
from OpenMediaMatch.blueprints.matching import (
    lookup_signal,
    lookup_signal_with_distance,
)
from OpenMediaMatch.utils.flask_utils import api_error_handler

from OpenMediaMatch.utils import dev_utils
from OpenMediaMatch import persistence
from OpenMediaMatch.storage.postgres.flask_utils import reset_tables


from threatexchange.exchanges.fetch_state import CollaborationConfigBase
from threatexchange.exchanges.impl.static_sample import StaticSampleSignalExchangeAPI
from threatexchange.exchanges.impl.fb_threatexchange_api import (
    FBThreatExchangeSignalExchangeAPI,
    FBThreatExchangeCollabConfig,
)


bp = Blueprint("development", __name__)
bp.register_error_handler(HTTPException, api_error_handler)


@bp.route("/query")
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

    include_distance = str_to_bool(request.args.get("include_distance", "false"))
    lookup_signal_func = (
        lookup_signal_with_distance if include_distance else lookup_signal
    )

    # Check if signal_type is an option in the map of hashes
    signal_type_name = request.args.get("signal_type")
    if signal_type_name is not None:
        if signal_type_name not in signal_type_to_signal_map:
            abort(
                400,
                f"Requested signal type '{signal_type_name}' is not supported for the provided "
                "media.",
            )
        return lookup_signal_func(
            signal_type_to_signal_map[signal_type_name], signal_type_name
        )
    return {
        "matches": list(
            itertools.chain(
                *map(
                    lambda x: lookup_signal_func(x[1], x[0])["matches"],
                    signal_type_to_signal_map.items(),
                ),
            )
        )
    }


@bp.route("/setup_sample_example", methods=["POST"])
def seed_sample():
    dev_utils.seed_sample()
    return redirect(url_for("ui.home"))


@bp.route("/setup_tx_example", methods=["POST"])
def setup_tx_example():
    storage = persistence.get_storage()
    storage.exchange_update(
        FBThreatExchangeCollabConfig(
            name="TX_EXAMPLE_COLLAB", privacy_group=1012185296055235
        ),
        create=True,
    )
    return redirect(url_for("ui.home"))


@bp.route("/seed_banks", methods=["POST"])
def seed_banks():
    dev_utils.seed_banks_random()
    return redirect(url_for("ui.home"))


@bp.route("/factory_reset", methods=["POST"])
def factory_reset():
    reset_tables()
    return redirect(url_for("ui.home"))
