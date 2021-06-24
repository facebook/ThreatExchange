#! /usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import os
import json
import time
import threading
import typing as t
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    """
    Request handler that counts the number of post request it receives.
    """

    # ToDo Currently multiple instances cannot operating without taking a lock on the class attribute
    threadLock: threading.Lock = threading.Lock()
    post_counter: int = 0

    def _set_response(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

    def do_GET(self):
        with Handler.threadLock:
            payload = {
                "message": "GET Received",
                "path": str(self.path),
                "headers": str(self.headers),
                "post_counter": str(Handler.post_counter),
            }
        self._set_response()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)

        payload = {
            "message": "POST Received",
            "path": str(self.path),
            "headers": str(self.headers),
            "body": str(post_data.decode("utf-8")),
        }
        with Handler.threadLock:
            Handler.post_counter += 1
        self._set_response()
        self.wfile.write(json.dumps(payload).encode("utf-8"))


def start_listening_web_server(
    hostname: str = "localhost",
    port: int = 8080,
    handler=Handler,
) -> ThreadingHTTPServer:
    with Handler.threadLock:
        Handler.post_counter = 0
    web_server = ThreadingHTTPServer((hostname, port), handler)
    server_thread = threading.Thread(target=web_server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    return web_server


if __name__ == "__main__":

    hostname = os.environ.get(
        "EXTERNAL_HOSTNAME",
        "localhost",
    )
    web_server = start_listening_web_server(hostname)
    ip, port = web_server.server_address

    print("Server started http://%s:%s" % (hostname, port))

    cmd = ""
    while cmd != "q":
        cmd = input("Enter 'q' to shutdown: ")

    web_server.shutdown()
    print("Server stopped.")
