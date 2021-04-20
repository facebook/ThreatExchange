# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json
import typing as t
from bottle import response, install

"""
Inspired by Java's JAX-RS standards and perhaps most sane web frameworks. Allows
you to specify the •type* of a view.

Sample usage:
>>> @dataclass
... class CupcakesResponse(JSONifiable):
...    num_cupcakes: int
...    flavor: string = int

...    def to_json(self) -> t.Dict:
...        return {
...            "num_cupcakes": self.num_cupcakes,
...            "flavor": self.flavor,
...        }

>>>@app.get("/all", apply=[jsoninator])
...def get_all_datasets() -> CupcakesResponse:
...    response.status_code = 200 # optional
...    return CupcakesResponse(12, "key_lime")
"""


class JSONifiable:
    def to_json(self) -> t.Dict:
        raise NotImplementedError


def jsoninator(view_fn: t.Callable[[int, int], JSONifiable]):
    """
    Bottle plugin which allows you to create 'typed' views.

    Views are expected to return an object which has a to_json method. The
    content_type header will be automatically set, but if you need to set
    anything else, eg. status code or other headers, continue to use
    `bottle.response`.
    """

    def wrapper(*args, **kwargs):
        body = view_fn(*args, **kwargs)
        response.content_type = "application/json"
        return json.dumps(body.to_json())

    return wrapper
