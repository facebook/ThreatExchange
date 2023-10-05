from flask import Blueprint, abort
from flask import request, redirect

from OpenMediaMatch.blueprints import matching, curation, hashing
from OpenMediaMatch.persistence import get_storage
from OpenMediaMatch.background_tasks import build_index
from OpenMediaMatch.database import db

bp = Blueprint("ui", __name__)


@bp.route("/create_bank", methods=["POST"])
def ui_create_bank():
    # content type from dropdown form
    bank_name = request.form.get("bank_name")
    if bank_name is None:
        abort(400, "Bank name is required")

    curation.bank_create_impl(bank_name)
    return redirect("/")


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
    return redirect("/")


@bp.route("/factory_reset", methods=["POST"])
def factory_reset():
    db.drop_all()
    db.create_all()
    return redirect("/")
