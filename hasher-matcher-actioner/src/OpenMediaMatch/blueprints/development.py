# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Development only routes for easily testing functionality end-to-end, all running on a single host.
"""

from flask import Blueprint
from flask import redirect, url_for
from werkzeug.exceptions import HTTPException

from OpenMediaMatch.utils.flask_utils import api_error_handler

from OpenMediaMatch.utils import dev_utils
from OpenMediaMatch import persistence
from OpenMediaMatch.storage.postgres.flask_utils import reset_tables


from threatexchange.exchanges.impl.fb_threatexchange_api import (
    FBThreatExchangeCollabConfig,
)


bp = Blueprint("development", __name__)
bp.register_error_handler(HTTPException, api_error_handler)


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
