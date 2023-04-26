import flask

app = flask.Flask(__name__)

@app.route("/")
def index():
    """
    Liveness/readiness check endpoint for your favourite Layer 7 load balancer
    """
    return "I-AM-ALIVE"


@app.route("/hash/image")
def hash_image():
    """
    Hash an image
    """
    image_url = flask.request.args.get('url')
    if image_url is None:
        flask.abort(400)

    return f"If this was implemented you'd be seeing the PDQ hash of the image at {image_url} here"
