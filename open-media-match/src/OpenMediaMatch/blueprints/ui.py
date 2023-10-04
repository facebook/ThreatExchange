import flask
import os
import requests

from flask import Blueprint, abort
from flask import request, redirect, url_for

from OpenMediaMatch.blueprints import matching, curation, hashing

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


@bp.route("/addcontent", methods=["POST"])
def addcontent():
    signaltypes = curation.get_all_signal_types()
    contenttypes = curation.get_all_content_types()
    banks = curation.banks_index()
    return flask.render_template(
        "index.html.j2",
        fileresult=True,
        signal=signaltypes,
        content=contenttypes,
        bankList=banks,
    )
