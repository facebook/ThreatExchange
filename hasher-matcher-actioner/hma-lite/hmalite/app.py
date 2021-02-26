import re
from flask import Flask, render_template, request, jsonify, send_from_directory
from hmalite.matcher import matcher_api
from threatexchange.signal_type import index, pdq_index
import os
import csv

app = Flask(__name__)
app.register_blueprint(matcher_api, url_prefix="/v1/hashes")


@app.route("/")
def index():
    files = os.listdir("hmalite/data/")
    return render_template("index.html", files=files)


@app.route("/data/<path:filename>", methods=["GET", "POST"])
def download(filename):
    return send_from_directory(directory="data", filename=filename)


@app.route("/upload_hashes", methods=["GET", "POST"])
def upload_hashes():
    if request.method == "POST":
        uploaded_file = request.files["data_file"]
        if uploaded_file.filename != "":
            filepath = os.path.join("hmalite/uploads", uploaded_file.filename)
            uploaded_file.save(filepath)
            create_index(filepath)
        return index()
    return "", 204

@app.route("/check_for_match", methods=["GET", "POST"])
def check_for_match():
    if request.method == "POST":
        hash = request.form["hash"]
        with open(os.path.join("hmalite/data", "data.index"), "rb") as f:
            index = pdq_index.PDQIndex.deserialize(f.read())
            results = index.query(hash)
            print(results)
        matches = []
        for result in results:
            matches.append(result.metadata)
        if len(matches) > 0:
            return jsonify({"matches": matches})


def create_index(filepath):
    with open(filepath, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        entries = []
        for row in reader:
            entries.append(((row["td_raw_indicator"], row)))
        index = pdq_index.PDQIndex.build(entries)
        with open(os.path.join("hmalite/data", "data.index"), "wb") as f:
            f.write(index.serialize(f))
