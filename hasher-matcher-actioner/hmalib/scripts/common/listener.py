#! /usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.

import os
import json
import datetime
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
    latency_lock: threading.Lock = threading.Lock()
    # ToDo do we want this to grow without bound or be limted to x most recent items?
    submission_latencies: t.List[
        t.Tuple[datetime.datetime, datetime.datetime, float]
    ] = []

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

        present = datetime.datetime.now()
        if content_id := json.loads(post_data).get("content_key"):
            try:
                submit_time = datetime.datetime.fromisoformat(
                    content_id.split("-time-")[1]
                )
                latency = present - submit_time
                with self.latency_lock:
                    self.submission_latencies.append(
                        (submit_time, present, latency.total_seconds())
                    )
            except ValueError and IndexError:
                pass


class Listener:
    def __init__(
        self,
        hostname: str = "localhost",
        port: int = 8080,
    ) -> None:
        self.hostname = hostname
        self.port = port
        self.web_server: t.Optional[ThreadingHTTPServer] = None

    def start_listening(self):
        if self.web_server:
            print(
                "Listener already started\nTo reset counter call `stop_listening` first."
            )

        with _Handler.count_lock:
            _Handler.post_counter = 0
        self.web_server = ThreadingHTTPServer((self.hostname, self.port), _Handler)
        server_thread = threading.Thread(target=self.web_server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        print(f"Listener server started http://{self.hostname}:{self.port}")

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
            return 0
        with _Handler.count_lock:
            return _Handler.post_counter

    def get_submission_latencies(
        self,
    ) -> t.List[t.Tuple[datetime.datetime, datetime.datetime, float]]:
        with _Handler.latency_lock:
            return _Handler.submission_latencies.copy()


if __name__ == "__main__":

    hostname = os.environ.get(
        "EXTERNAL_HOSTNAME",
        "localhost",
    )
    listener = Listener(hostname)
    listener.start_listening()

    cmd = ""
    while cmd != "q":
        cmd = input("Enter 'q' to shutdown: ")

    listener.stop_listening()
