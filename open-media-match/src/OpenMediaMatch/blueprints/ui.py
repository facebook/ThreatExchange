# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t

from flask import Blueprint, abort, render_template, current_app
from flask import request, redirect

from OpenMediaMatch.blueprints import matching, curation, hashing
from OpenMediaMatch.persistence import get_storage
from OpenMediaMatch.background_tasks import build_index
from OpenMediaMatch.storage.postgres.database import db

bp = Blueprint("ui", __name__)


def _index_info() -> dict[str, dict[str, t.Any]]:
    index = curation.signal_type_index_status()
    for name, dat in index.items():
        progress = 100
        progress_label = "Up to date"
        if dat["index_out_of_date"]:
            a = dat["index_size"]
            b = dat["db_size"]
            pct = min(a, b) * 100 / max(1, a, b)
            progress = int(min(90, pct))
            progress_label = f"{min(a, b)}/{max(a, b)} ({pct:.2f}%)"
        index[name]["progress_pct"] = progress
        index[name]["progress_label"] = progress_label
        index[name]["progress_style"] = "bg-success" if progress == 100 else ""
    return index


def _collab_info() -> dict[str, dict[str, t.Any]]:
    collabs = get_storage().get_collaborations()
    return {
        name: {
            "api": cfg.api,
            "bank": name.removeprefix("c-"),
            "progress_style": "",
            "progress_pct": 0,
            "progress_label": "Not yet implemented",
        }
        for name, cfg in collabs.items()
    }


@bp.route("/")
def home():
    """
    Sanity check endpoint showing a basic status page
    """

    template_vars = {
        "signal": curation.get_all_signal_types(),
        "content": curation.get_all_content_types(),
        "bankList": curation.banks_index(),
        "production": current_app.config.get("PRODUCTION", True),
        "index": _index_info(),
        "collabs": _collab_info(),
    }
    return render_template("bootstrap.html.j2", **template_vars)


@bp.route("/create_bank", methods=["POST"])
def ui_create_bank():
    # content type from dropdown form
    bank_name = request.form.get("bank_name")
    if bank_name is None:
        abort(400, "Bank name is required")
    curation.bank_create_impl(bank_name)
    return redirect("./")


@bp.route("/query", methods=["POST"])
def upload():
    signals = hashing.hash_media_post_impl()

    banks = {
        b
        for st_name, signal in signals.items()
        for b in matching.lookup(signal, st_name)
    }

    return {"hashes": signals, "banks": sorted(banks)}


@bp.route("/rebuild_index", methods=["POST"])
def rebuild_index():
    st_name = request.form.get("signal_type")
    storage = get_storage()
    if st_name is not None:
        st = storage.get_signal_type_configs().get(st_name)
        if st is None:
            abort(404, f"No such signal type '{st_name}'")
        if not st.enabled:
            abort(400, f"Signal type {st_name} is disabled")
        build_index.build_index(st.signal_type)
        return {}
    build_index.build_all_indices(storage, storage, storage)
    return redirect("./")


@bp.route("/factory_reset", methods=["POST"])
def factory_reset():
    db.drop_all()
    db.create_all()
    return redirect("./")
