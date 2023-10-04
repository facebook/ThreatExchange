import flask
import os
import requests

from flask import Blueprint
from flask import request

from OpenMediaMatch.blueprints import matching, curation, hashing

bp = Blueprint("ui", __name__)


@bp.route("/query", methods=["POST"])
def upload():
    hash = hashing.hash_media_post()
    # The hash function returns an object with a single key (the signal_type) and value (the signal)
    signal_type = list(hash.keys())[0]
    signal = hash[signal_type]

    banks = matching.lookup(signal, signal_type)
    
    return {
        "hashes": hash,
        "banks": banks
    }
