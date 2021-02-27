# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

from flask import Flask, render_template, request, jsonify, send_from_directory
from hmalite.matcher import matcher_api
from threatexchange.signal_type import index, pdq_index
from threatexchange.hashing.pdq_hasher import pdq_from_file
import os
import csv

app = Flask(__name__)
app.register_blueprint(matcher_api, url_prefix="/v1/hashes")

# TODO Move to APP Config
UPLOADS_FOLDER = "hmalite/uploads"
INDEX_FOLDER = "hmalite/data"
INDEX_FILENAME = "data.index"


@app.route("/")
def index():
    files = os.listdir("hmalite/data/")
    return render_template("index.html", files=files)


@app.route("/upload_hashes", methods=["GET", "POST"])
def upload_hashes():
    if request.method == "POST":
        uploaded_file = request.files["data_file"]
        if uploaded_file.filename != "":
            filepath = os.path.join(UPLOADS_FOLDER, uploaded_file.filename)
            uploaded_file.save(filepath)
            create_index(filepath)
        return index()
    return "", 204


@app.route("/check_for_match_hash", methods=["GET", "POST"])
def check_for_match_hash():
    if request.method == "POST":
        hash = request.form["hash"]
        # TODO field validation (if give something not a pdq hash)
        matches = query_index(hash)
        return render_template("results.html", result=matches, hash=hash)


@app.route("/check_for_match_image", methods=["GET", "POST"])
def check_for_match_image():
    if request.method == "POST":
        uploaded_file = request.files["photo"]
        if uploaded_file.filename != "":
            file_path = os.path.join(UPLOADS_FOLDER, uploaded_file.filename)
            uploaded_file.save(file_path)

        with open(file_path, "rb") as f:
            hash, _ = pdq_from_file(file_path)
            matches = query_index(hash)
            return render_template(
                "results.html", result=matches, hash=hash, image=uploaded_file.filename
            )


# Utility Methods
def create_index(filepath):
    with open(filepath, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        entries = []
        for row in reader:
            entries.append(((row["td_raw_indicator"], row)))
        index = pdq_index.PDQIndex.build(entries)
        with open(os.path.join(INDEX_FOLDER, INDEX_FILENAME), "wb") as f:
            index.serialize(f)


def query_index(hash):
    with open(os.path.join(INDEX_FOLDER, INDEX_FILENAME), "rb") as f:
        index = pdq_index.PDQIndex.deserialize(f.read())
        results = index.query(hash)
        matches = []
        for result in results:
            matches.append(result.metadata)
        return matches


# Make files available
@app.route("/data/<path:filename>", methods=["GET", "POST"])
def download(filename):
    return send_from_directory(directory=INDEX_FOLDER, filename=filename)


@app.route("/uploads/<filename>")
def upload(filename):
    return send_from_directory(directory=UPLOADS_FOLDER, filename=filename)
