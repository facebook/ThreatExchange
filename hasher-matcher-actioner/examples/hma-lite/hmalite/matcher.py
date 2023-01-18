# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t

from flask import Blueprint, request, jsonify, current_app
from hmalite import index
from hmalite.config import HmaLiteConfig
from threatexchange.signal_type.index import IndexMatch

matcher_api = Blueprint("matcher_api", __name__)


@matcher_api.route("/query", methods=["GET", "POST"])
def matcher_query():
    local_index = index.get_local_index()

    if request.method == "POST":
        hashes = request.json["hashes"]

        matches = {}

        for pdq in hashes:
            matches[pdq] = index_query_to_dict(local_index.query(pdq))

        return jsonify(results=matches)
    else:
        pdq = request.args.get("hash")
        if not pdq:
            return "requires a hash", 400
        results = index_query_to_dict(local_index.query(pdq))
        return jsonify(match=bool(results), result=results)


def index_query_to_dict(mm: t.Iterable[IndexMatch]):
    return [{"distance": m.distance, "data": m.metadata} for m in mm]
