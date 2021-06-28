#! /usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import os
import json
import time
import threading
import requests
import typing as t
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class _Handler(BaseHTTPRequestHandler):
    """
    Request handler that counts the number of post request it receives.
    Currently multiple instances cannot operating without taking a lock on the class attribute
    """

    count_lock: threading.Lock = threading.Lock()
    post_counter: int = 0

    def _set_response(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

    def log_message(self, format, *args):
        # Override log method to keep test output clear
        return

    def do_GET(self):
        with _Handler.count_lock:
            payload = {
                "message": "GET Received",
                "path": str(self.path),
                "headers": str(self.headers),
                "post_counter": str(_Handler.post_counter),
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
        with _Handler.count_lock:
            _Handler.post_counter += 1
        self._set_response()
        self.wfile.write(json.dumps(payload).encode("utf-8"))


class Listener:
    def __init__(self) -> None:
        self.web_server: t.Optional[ThreadingHTTPServer] = None

    def start_listening(
        self,
        hostname: str = "localhost",
        port: int = 8080,
    ):
        if self.web_server:
            print(
                "Listener already started\nTo reset counter call `stop_listening` first."
            )

        with _Handler.count_lock:
            _Handler.post_counter = 0
        self.web_server = ThreadingHTTPServer((hostname, port), _Handler)
        server_thread = threading.Thread(target=self.web_server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        self.server_url = f"http://{hostname}:{port}"
        print(f"Listener server started {self.server_url}")

    def stop_listening(self):
        if self.web_server:
            self.web_server.shutdown()
            print("Listener server stopped")
            self.web_server = None
        else:
            print("Listener server not found")

    def get_post_request_count(self) -> int:
        if not self.web_server:
            print("Warning: Listener server not found")
            return -1
        with _Handler.count_lock:
            return _Handler.post_counter


if __name__ == "__main__":

    hostname = os.environ.get(
        "EXTERNAL_HOSTNAME",
        "localhost",
    )
    listener = Listener()
    listener.start_listening(hostname, port=8080)

    cmd = ""
    while cmd != "q":
        cmd = input("Enter 'q' to shutdown: ")

    listener.stop_listening()
