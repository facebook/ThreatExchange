# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Development only routes for easily testing functionality end-to-end, all running on a single host.
"""

import gc
import os

from flask import jsonify, redirect, request, url_for
from flask_openapi3 import APIBlueprint
from flask_openapi3.models import Tag
from werkzeug.exceptions import HTTPException

from OpenMediaMatch.utils.flask_utils import api_error_handler

from OpenMediaMatch.utils import dev_utils
from OpenMediaMatch import persistence
from OpenMediaMatch.background_tasks import fetcher
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
    "/run_fetch",
    tags=[Tag(name="Development")],
    responses={"200": SuccessResponse, "302": {"description": "Redirect to exchanges"}},
    summary="Run fetch now",
    description="Trigger the exchange fetcher once immediately (same as background task). Use for debugging.",
)
def run_fetch():
    storage = persistence.get_storage()
    fetcher.fetch_all(storage, storage.get_signal_type_configs())
    return redirect(url_for("ui.exchanges"))


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


@bp.get(
    "/pympler",
    tags=[Tag(name="Development")],
    summary="Heap summary (object-type histogram)",
    description=(
        "Returns top-N live Python object types by retained bytes. "
        "Used by the memory-leak repro script to diff per-type growth over time. "
        "Only registered when OMM_ENABLE_PYMPLER=1 (it imports and walks the full heap)."
    ),
)
def pympler_summary():
    if os.environ.get("OMM_ENABLE_PYMPLER") != "1":
        return jsonify({"error": "pympler endpoint disabled"}), 404
    from pympler import muppy, summary  # imported lazily

    top = int(request.args.get("top", "50"))
    gc.collect()
    all_objs = muppy.get_objects()
    rows = summary.summarize(all_objs)
    rows.sort(key=lambda r: r[2], reverse=True)
    return jsonify(
        {
            "gc_count": list(gc.get_count()),
            "total_tracked_objects": len(all_objs),
            "top": [
                {"type": r[0], "count": r[1], "total_bytes": r[2]}
                for r in rows[:top]
            ],
        }
    )
