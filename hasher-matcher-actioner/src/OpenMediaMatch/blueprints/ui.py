# Copyright (c) Meta Platforms, Inc. and affiliates.

import time
import typing as t

from flask import Blueprint, abort, render_template, current_app
from flask import request, redirect

from OpenMediaMatch.blueprints import matching, curation, hashing
from OpenMediaMatch.blueprints.matching import MatchWithDistance
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
    contains_seed_bank_0 = any(bank.name == "SEED_BANK_0" for bank in bank_list)
    contains_seed_bank_1 = any(bank.name == "SEED_BANK_1" for bank in bank_list)

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
        "signal": curation.get_all_signal_types(),
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
    bypass_enabled_ratio = (
        request.form.get("bypass_enabled_ratio", "true").lower() == "true"
    )

    return _perform_lookup_with_details(signals, bypass_enabled_ratio)


@bp.route("/query_url", methods=["POST"])
def query_url():
    """
    Query by URL instead of file upload.

    Input (form data):
    - url: URL to the content
    - content_type: Type of content (photo, video, etc.)
    - bypass_enabled_ratio: Whether to bypass enabled ratio check
    """
    current_app.logger.debug("[query_url] hashing input from URL")

    # Get parameters from form data
    url = request.form.get("url")
    content_type = request.form.get("content_type")

    if not url:
        abort(400, "URL is required")
    if not content_type:
        abort(400, "Content type is required")

    # Hash the URL content
    try:
        signals = _hash_url_for_search(url, content_type)
    except Exception as e:
        abort(400, f"Failed to hash URL content: {str(e)}")

    # Get bypass parameter from form data
    bypass_enabled_ratio = (
        request.form.get("bypass_enabled_ratio", "true").lower() == "true"
    )

    return _perform_lookup_with_details(signals, bypass_enabled_ratio)


@bp.route("/query_hash", methods=["POST"])
def query_hash():
    """
    Query by hash value instead of file upload or URL.

    Input (form data):
    - signal_type: Type of signal (pdq, tmk, etc.)
    - signal_value: Hash value to search for
    - bypass_enabled_ratio: Whether to bypass enabled ratio check
    """
    current_app.logger.debug("[query_hash] performing lookup by hash")

    # Get parameters from form data
    signal_type = request.form.get("signal_type")
    signal_value = request.form.get("signal_value")

    if not signal_type:
        abort(400, "Signal type is required")
    if not signal_value:
        abort(400, "Signal value is required")

    # Create a single hash entry for the lookup
    signals = {signal_type: signal_value}

    # Get bypass parameter from form data
    bypass_enabled_ratio = (
        request.form.get("bypass_enabled_ratio", "true").lower() == "true"
    )

    return _perform_lookup_with_details(signals, bypass_enabled_ratio)


def _perform_lookup_with_details(
    signals: dict[str, str], bypass_enabled_ratio: bool
) -> dict:
    """
    Common lookup function that returns detailed match information including
    content IDs and distances for all query types.
    """
    current_app.logger.debug("[_perform_lookup_with_details] performing lookup")

    # Get all matches with detailed information
    all_matches: list[dict[str, t.Any]] = []
    bank_names = set()

    for st_name, signal in signals.items():
        bank_matches = matching.lookup(
            signal, st_name, bypass_coinflip=bypass_enabled_ratio
        )
        for bank_name, matches in bank_matches.items():
            bank_names.add(bank_name)
            for match in matches:
                all_matches.append(
                    {
                        "bank_name": bank_name,
                        "content_id": match["bank_content_id"],
                        "distance": match["distance"],
                        "signal_type": st_name,
                        "signal_value": signal,
                    }
                )

    # Sort matches by distance (closest matches first)
    all_matches.sort(
        key=lambda x: (
            float(t.cast(str, x["distance"]))
            if t.cast(str, x["distance"]).replace(".", "").isdigit()
            else float("inf")
        )
    )

    return {"hashes": signals, "banks": sorted(bank_names), "matches": all_matches}


def _hash_url_for_search(url: str, content_type: str) -> dict[str, str]:
    """Utility function to hash a URL for content search."""
    try:
        # Call the hashing utility function directly
        return hashing.hash_url_content(url)
    except ValueError as e:
        abort(400, f"Failed to hash URL: {str(e)}")
    except Exception as e:
        abort(500, f"Unexpected error hashing URL: {str(e)}")


def _find_match_content_ids_by_hashes(
    hashes: dict[str, str], bank_name: str
) -> tuple[set[int], list[dict]]:
    """Utility function to find matches for multiple hashes in a specific bank."""
    content_ids = set()
    matches = []

    for signal_type, signal_value in hashes.items():
        bank_matches = matching.lookup(signal_value, signal_type, bypass_coinflip=True)
        if bank_name in bank_matches:
            for match in bank_matches[bank_name]:
                content_ids.add(match["bank_content_id"])
                matches.append(
                    {
                        "signal_type": signal_type,
                        "signal_value": signal_value,
                        "content_id": match["bank_content_id"],
                        "distance": match["distance"],
                    }
                )

    return content_ids, matches


def _find_match_content_ids_by_hash(
    signal_type: str, signal_value: str, bank_name: str
) -> tuple[set[int], list[dict]]:
    """Utility function to find matches for a single hash in a specific bank."""
    bank_matches = matching.lookup(signal_value, signal_type, bypass_coinflip=True)
    content_ids = set()
    matches = []

    if bank_name in bank_matches:
        for match in bank_matches[bank_name]:
            content_ids.add(match["bank_content_id"])
            matches.append(
                {
                    "signal_type": signal_type,
                    "signal_value": signal_value,
                    "content_id": match["bank_content_id"],
                    "distance": match["distance"],
                }
            )

    return content_ids, matches


@bp.route("/bank/<bank_name>/content/find", methods=["POST"])
def bank_find_content(bank_name: str):
    """
    Find content in a bank by URL or hash to get content IDs for removal.

    Input (JSON):
    - For URL: {"url": "https://...", "content_type": "photo"}
    - For hash: {"signal_type": "pdq", "signal_value": "abc123..."}

    Output:
    - {"content_ids": [1, 2, 3], "matches": [...]}
    """
    storage = get_storage()
    bank = storage.get_bank(bank_name)
    if not bank:
        abort(404, f"bank '{bank_name}' not found")

    data = request.get_json()
    if not data:
        abort(400, "JSON payload required")

    # Handle URL-based search
    if "url" in data:
        content_type = data.get("content_type")
        if not content_type:
            abort(400, "content_type required when searching by URL")

        hashes = _hash_url_for_search(data["url"], content_type)
        content_ids, matches = _find_match_content_ids_by_hashes(hashes, bank_name)

    # Handle hash-based search
    elif "signal_type" in data and "signal_value" in data:
        signal_type = data["signal_type"]
        signal_value = data["signal_value"]
        content_ids, matches = _find_match_content_ids_by_hash(
            signal_type, signal_value, bank_name
        )

    else:
        abort(
            400,
            "Either 'url' with 'content_type' or 'signal_type' with 'signal_value' required",
        )

    return {
        "content_ids": list(content_ids),
        "matches": matches,
        "bank_name": bank_name,
    }
