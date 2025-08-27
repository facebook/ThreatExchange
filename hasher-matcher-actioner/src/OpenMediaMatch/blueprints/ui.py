# Copyright (c) Meta Platforms, Inc. and affiliates.

import time
import typing as t

from flask import Blueprint, abort, render_template, current_app
from flask import request, redirect

from OpenMediaMatch.blueprints import matching, curation, hashing
from OpenMediaMatch.persistence import get_storage
from OpenMediaMatch.utils.time_utils import duration_to_human_str

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


def _api_cls_info() -> dict[str, dict[str, t.Any]]:
    return {
        name: {
            "auth_icon": (
                ""
                if not cfg.supports_auth
                else ("🔒" if cfg.credentials is None else "🔑")
            ),
            "auth_title": (
                ""
                if not cfg.supports_auth
                else (
                    'title="May need credentials"'
                    if cfg.credentials is None
                    else 'title="Has credentials"'
                )
            ),
        }
        for name, cfg in get_storage().exchange_apis_get_configs().items()
    }


def _collab_info() -> dict[str, dict[str, t.Any]]:
    storage = get_storage()
    collabs = storage.exchanges_get()
    ret = {}
    for name, cfg in collabs.items():
        # serial db fetch, yay!
        fetch_status = storage.exchange_get_fetch_status(name)
        progress_label = ""
        progress = 50
        if fetch_status.last_fetch_complete_ts is None:
            progress = 0
        elif fetch_status.up_to_date:
            progress_label = "Up to date!"
            progress = 100
        # TODO add some idea of progress to the checkpoint class

        progress_style = "bg-success" if progress == 100 else "bg-info"
        if fetch_status.last_fetch_succeeded is False:
            progress_style = "bg-danger"
            progress_label = "Error on fetch!"
            progress = min(90, progress)

        last_run_time = fetch_status.last_fetch_complete_ts
        if fetch_status.running_fetch_start_ts is not None:
            progress_style += " progress-bar-striped progress-bar-animated"
            last_run_time = fetch_status.running_fetch_start_ts

        if not cfg.enabled:
            progress_style = "bg-secondary"

        last_run_text = "Never"
        if last_run_time is not None:
            diff = max(int(time.time() - last_run_time), 0)
            last_run_text = duration_to_human_str(diff, terse=True)
            last_run_text += " ago"

        ret[name] = {
            "api": cfg.api,
            "bank": name.removeprefix("c-"),
            "enabled": cfg.enabled,
            "count": fetch_status.fetched_items,
            "progress_style": progress_style,
            "progress_pct": progress,
            "progress_label": progress_label,
            "last_run_text": last_run_text,
        }
    return ret


@bp.route("/")
def home():
    """
    UI Landing page
    """

    # Check if SEED_BANK_0 and SEED_BANK_1 exist yet
    bank_list = curation.banks_index()
    contains_seed_bank_0 = any(
        bank.name == "SEED_BANK_0" for bank in bank_list)
    contains_seed_bank_1 = any(
        bank.name == "SEED_BANK_1" for bank in bank_list)

    template_vars = {
        "signal": curation.get_all_signal_types(),
        "content": curation.get_all_content_types(),
        "exchange_apis": _api_cls_info(),
        "production": current_app.config.get("PRODUCTION", False),
        "index": _index_info(),
        "collabs": _collab_info(),
        "is_banks_seeded": contains_seed_bank_0 and contains_seed_bank_1,
    }
    return render_template("bootstrap.html.j2", page="home", **template_vars)


@bp.route("/banks")
def banks():
    """
    Bank management page
    """
    template_vars = {
        "bankList": curation.banks_index(),
        "content": curation.get_all_content_types(),
    }
    return render_template("bootstrap.html.j2", page="banks", **template_vars)


@bp.route("/exchanges")
def exchanges():
    """
    Exchange management page
    """
    template_vars = {
        "exchange_apis": _api_cls_info(),
        "collabs": _collab_info(),
    }
    return render_template("bootstrap.html.j2", page="exchanges", **template_vars)


@bp.route("/match")
def match_dbg():
    """
    Bank management page
    """
    return render_template("bootstrap.html.j2", page="match_dbg")


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
    current_app.logger.debug("[query] hashing input")
    signals = hashing.hash_media_from_form_data()

    # Get bypass parameter from form data (default to True for backward compatibility)
    bypass_enabled_ratio = request.form.get(
        'bypass_enabled_ratio', 'true').lower() == 'true'
    current_app.logger.debug(
        f"[query] bypass_enabled_ratio: {bypass_enabled_ratio}")

    current_app.logger.debug("[query] performing lookup")
    banks = {
        b
        for st_name, signal in signals.items()
        for b in matching.lookup(signal, st_name, bypass_coinflip=bypass_enabled_ratio)
    }

    return {"hashes": signals, "banks": sorted(banks)}
