# Copyright (c) Meta Platforms, Inc. and affiliates.

import unittest
import json
from dataclasses import asdict, dataclass
from webtest import TestApp as TApp  # TestApp gets detected as a test
from bottle import Bottle

from hmalib.lambdas.api.middleware import jsoninator, JSONifiable, DictParseable


@dataclass
class ResponseClass(JSONifiable):
    foo: str
    bar: int

    def to_json(self):
        return {"foo": self.foo, "bar": self.bar}


@dataclass
class RequestBody(DictParseable):
    foo: str
    bar: int

    @classmethod
    def from_dict(cls, d):
        return cls(d["foo"], d["bar"])


mock_app = Bottle()


@mock_app.route("/response-is-json/", apply=[jsoninator])
def response_is_json() -> ResponseClass:
    return ResponseClass("X", 10)


@mock_app.post("/response-and-request-is-json/", apply=[jsoninator(RequestBody)])
def response_and_request_is_json(request: RequestBody) -> ResponseClass:
    assert isinstance(request, RequestBody)
    assert request.foo == "X"
    assert request.bar == 10
    return ResponseClass("C", 20)


if __name__ == "__main__":
    mock_app.run(port=9090)


class MiddlewareUnitTest(unittest.TestCase):
    def test_json_response_body(self):
        app = TApp(mock_app)

        response = app.get("/response-is-json/")
        self.assertEqual(response.status, "200 OK")
        self.assertEqual(response.body, b'{"foo": "X", "bar": 10}')

    def test_json_response_body_and_request_payload(self):
        app = TApp(mock_app)

        # The asserts are actually inside the route handler, so no asserts after
        # this statement.
        response = app.post(
            "/response-and-request-is-json/",
            params=json.dumps({"foo": "X", "bar": 10}),
            content_type="application/json",
        )
