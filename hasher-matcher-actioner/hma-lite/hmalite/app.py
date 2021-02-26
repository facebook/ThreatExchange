from flask import Flask

from hmalite.matcher import matcher_api

app = Flask(__name__)
app.register_blueprint(matcher_api, url_prefix="/v1/hashes")

@app.route('/')
def hello_world():
    return 'Hello, from the threatexchange API!'
