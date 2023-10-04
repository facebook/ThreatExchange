import flask
import os
import requests

from flask import Blueprint
from flask import request

from OpenMediaMatch.blueprints import matching, curation

bp = Blueprint("ui", __name__)


@bp.route("/query", methods=["POST"])
def upload():
    signaltypes = curation.get_all_signal_types()
    contenttypes = curation.get_all_content_types()
    banks = curation.banks_index()
    # content type from dropdown form
    contenttype = request.form.get("media")
    f = request.files["file"]
    f.save(f.filename)
    files = {
        contenttype: open(f.filename, "rb"),
    }
    # returns a dictionary of {'signaltype' : 'hash'}

    r = requests.post("http://localhost:5000/h/hash", files=files)
    rjson = r.json()
    for key, value in rjson.items():
        matches = matching.lookup_signal(value, key)
        matcheslist = matches["matches"]
    os.remove(f.filename)
    return flask.render_template(
        "index.html.j2",
        name=f.filename,
        matches=matcheslist,
        fileresult=True,
        signal=signaltypes,
        content=contenttypes,
        bankList=banks,
    )
