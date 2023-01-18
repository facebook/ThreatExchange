# Copyright (c) Meta Platforms, Inc. and affiliates.

import csv
import os
import os.path
import shutil

from flask import Flask, render_template, request, jsonify, send_from_directory
from hmalite.config import HmaLiteDevConfig, HmaLiteProdConfig
from hmalite.matcher import matcher_api
from hmalite.index import reset_index, get_local_index
from threatexchange.hashing.pdq_hasher import pdq_from_file
from threatexchange.signal_type import pdq_index


app = Flask(__name__)
app.register_blueprint(matcher_api, url_prefix="/v1/hashes")

# Set up those configs
if app.config["ENV"] == "production":
    config_cls = HmaLiteProdConfig
    app.config.from_object(HmaLiteProdConfig())
else:
    config_cls = HmaLiteDevConfig
config_helper = config_cls.init_with_environ()
app.config.from_object(config_helper)

if config_helper.DEBUG:
    app.logger.info("Config Values:")
    for name in config_cls._fields:
        app.logger.info("%s = %s", name, app.config[name])


#################### VARIOUS ENDPOINTS ####################


@app.route("/")
def index():
    files = []
    if config_helper.local_index_file:
        files = [config_helper.local_index_file]
    return render_template("index.html", files=files)


@app.route("/upload_hashes", methods=["GET", "POST"])
def upload_hashes():
    if request.method == "POST":
        uploaded_file = request.files["data_file"]
        if uploaded_file.filename != "":
            filepath = os.path.join(config_helper.upload_folder, uploaded_file.filename)
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
            file_path = os.path.join(
                config_helper.upload_folder, uploaded_file.filename
            )
            uploaded_file.save(file_path)

        with open(file_path, "rb") as f:
            hash, _ = pdq_from_file(file_path)
            matches = query_index(hash)
            return render_template(
                "results.html",
                result=matches,
                hash=hash,
                image=uploaded_file.filename,
            )


def create_index(filepath):
    with open(filepath, newline="") as csvfile:
        sample = csvfile.read(1024)
        csvfile.seek(0)

        # try and guess the format
        sniffer = csv.Sniffer()
        key = ""
        has_header = False
        try:
            has_header = sniffer.has_header(sample)
        except csv.Error:
            pass
        if has_header:
            reader = csv.DictReader(csvfile)
        else:
            reader = csv.DictReader(csvfile, fieldnames=["hash"], restkey="meta")

        # Try and guess what column has the hash
        key = reader.fieldnames[0]
        for pref in ("td_raw_indicator", "indicator", "hash", "pdq"):
            if pref in reader.fieldnames:
                key = pref
                break

        app.logger.info("Read CSV file, key=%s", key)

        entries = []
        for row in reader:
            entries.append((row[key], row))

    index = pdq_index.PDQIndex.build(entries)
    app.logger.info(
        "writing index of size %d from %s to %s",
        len(entries),
        filepath,
        config_helper.local_index_file_path,
    )
    with open(config_helper.local_index_file_path, "wb") as f:
        index.serialize(f)
    # Thanks to the miracle of the GIL, this is (mostly) safe!
    # Flask also aggressively threadlocals everything
    reset_index(index)


def query_index(hash):
    # Grab a local copy in case it gets replaced mid-request
    index = get_local_index()
    results = index.query(hash)
    matches = []
    for result in results:
        matches.append(result.metadata)
    app.logger.info("query against %d, find %d", len(index), len(matches))
    return matches


# Make files available
@app.route("/data/<path:filename>", methods=["GET", "POST"])
def download(filename):
    return send_from_directory(directory=INDEX_FOLDER, filename=filename)


@app.route("/uploads/<filename>")
def upload(filename):
    return send_from_directory(directory=config_helper.upload_folder, filename=filename)


#################### INITIAL SETUP ####################

# Create required directories
config_helper.create_dirs()

# Pre-load data if available
csv_f, index_f = config_helper.starting_index_files
if index_f and index_f != config_helper.local_index_file_path:
    app.logger.info("Starting available at %s, loading", index_f)
    load_index(index_f)
    shutil.copy(index_f, config_helper.local_index_file_path)
elif csv_f:
    app.logger.info("CSV available at %s", csv_f)
    create_index(csv_f)
