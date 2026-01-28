# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Development only routes for easily testing functionality end-to-end, all running on a single host.
"""

from flask_openapi3 import APIBlueprint
from flask_openapi3.models import Tag
from flask import redirect, url_for
from werkzeug.exceptions import HTTPException

from OpenMediaMatch.utils.flask_utils import api_error_handler

from OpenMediaMatch.utils import dev_utils
from OpenMediaMatch import persistence
from OpenMediaMatch.storage.postgres.flask_utils import reset_tables
from OpenMediaMatch.schemas.shared import SuccessResponse


from threatexchange.exchanges.impl.fb_threatexchange_api import (
    FBThreatExchangeCollabConfig,
)

bp = APIBlueprint("development", __name__, url_prefix="/dev")
bp.register_error_handler(HTTPException, api_error_handler)


@bp.post(
    "/setup_sample_example",
    tags=[Tag(name="Development")],
    responses={"302": {"description": "Redirect to UI"}},
    summary="Setup sample data",
    description="Add sample data API connection for development",
)
def seed_sample():
    dev_utils.seed_sample()
    return redirect(url_for("ui.home"))


@bp.post(
    "/setup_tx_example",
    tags=[Tag(name="Development")],
    responses={"200": SuccessResponse},
    summary="Setup ThreatExchange example",
    description="Setup ThreatExchange example configuration",
)
def setup_tx_example():
    storage = persistence.get_storage()
    storage.exchange_update(
        FBThreatExchangeCollabConfig(
            name="TX_EXAMPLE_COLLAB", privacy_group=1012185296055235
        ),
        create=True,
    )
    return redirect(url_for("ui.home"))


@bp.post(
    "/seed_banks",
    tags=[Tag(name="Development")],
    responses={"302": {"description": "Redirect to UI"}},
    summary="Seed random banks",
    description="Seed banks with random content for development testing",
)
def seed_banks():
    dev_utils.seed_banks_random()
    return redirect(url_for("ui.home"))


@bp.post(
    "/factory_reset",
    tags=[Tag(name="Development")],
    responses={"302": {"description": "Redirect to UI"}},
    summary="Factory reset",
    description="⚠️ Reset all database tables - USE WITH CAUTION",
)
def factory_reset():
    reset_tables()
    return redirect(url_for("ui.home"))
