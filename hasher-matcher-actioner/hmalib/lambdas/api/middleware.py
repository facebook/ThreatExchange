# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json
import typing as t
import bottle

from hmalib.common.logging import get_logger

logger = get_logger(__name__)

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


You can also specify the type of the request payload. If the request
Content-Type is application/json and it can be parsed into the shape requested,
your view will be called. Else, a 400 Bad request will be sent to the client.

Sample usage:
>>> @dataclass
... class CupcakesRequest(DictParseable):
...   @classmethod
...   def from_dict(cls, d: t.Dict) -> 'CupcakesRequest':
...     return CupcakesRequest(...)
...
>>> @app.post("/order-cupcakes/", apply=[jsoninator(CupcakesRequest)])
... def order_cupcakes(request:CupcakesRequest) -> CupcakesResponse:
...    <do stuff with request>
"""

# This module is tested in ./tests/test_middleware.py. You can also refer to
# that for sample usage.


class JSONifiable:
    def to_json(self) -> t.Dict:
        raise NotImplementedError


class DictParseable:
    @classmethod
    def from_dict(cls, d: t.Dict) -> "DictParseable":
        # Someday, include a vanilla de-serializer that uses dataclasses.fields
        # to construct a dataclass on the fly.
        raise NotImplementedError


def jsoninator(
    view_fn_or_request_type: t.Union[
        t.Callable[[int, int], JSONifiable], t.Type[DictParseable]
    ]
):
    """
    Bottle plugin which allows you to create 'typed' views.

    Views are expected to return an object which has a to_json method. The
    content_type header will be automatically set, but if you need to set
    anything else, eg. status code or other headers, continue to use
    `bottle.response`.

    If request type provided like jsoninator(RequestType), will de-serialize
    request payload into the first argument to the view function.
    """

    # I feel like I'm doing a lot of work to support a common API for typed
    # request payloads and untyped request payloads.  All this could be avoided
    # by having `jsoninator` and `jsoninator_typed_request(RequestType)`, but
    # meh! This looks shinier. All the complexity is hidden behind a single
    # method call.

    # Super verbose description of decorator BEGINS

    # A decorator is just a function that returns another function where the
    # returned function has some semantics. [Link to decorators
    # tutorial](https://realpython.com/primer-on-python-decorators/) If you are
    # familiar with decorators, continue reading this comment.

    # When you add jsoninator without arguments to bottle's apply=[..] list, it will
    # call jsoninator with the view function. As is typical with decorators.

    # When you add jsoninator with some arguments, python will first execute the
    # function, and then use the return value as a decorator.

    # Super verbose description of decorator ENDS

    # Can't use isinstance because Class types are t.Callable as well. So,
    # instead use the from_dict class method to determine if this is a decorator
    # for a typed request
    if hasattr(view_fn_or_request_type, "from_dict"):
        # Yes, it is a typed request style invocation, so cast to appropriate
        # types.
        request_type: DictParseable = t.cast(DictParseable, view_fn_or_request_type)

        def _jsoninantor_internal_for_typed_request_objects(
            view_fn: t.Callable[[int, int], t.Type[JSONifiable]]
        ):
            def wrapper(*args, **kwargs):
                try:
                    # Try to extract request
                    request_object = request_type.from_dict(bottle.request.json)
                except Exception as e:
                    logger.error(
                        "Failed to deserialize JSON for type: %s", str(request_type)
                    )
                    logger.exception(e)
                    bottle.response.status_code = 400
                    return "Could not parse JSON."

                response_object = view_fn(request_object, *args, **kwargs)

                bottle.response.content_type = "application/json"
                return json.dumps(response_object.to_json())

            return wrapper

        return _jsoninantor_internal_for_typed_request_objects

    else:
        # It is a typed response payload style invocation, so cast to approriate
        # type.
        view_fn: t.Callable[[int, int], JSONifiable] = t.cast(
            t.Callable[[int, int], JSONifiable], view_fn_or_request_type
        )

        def wrapper(*args, **kwargs):
            body = view_fn(*args, **kwargs)

            bottle.response.content_type = "application/json"
            return json.dumps(body.to_json())

        return wrapper
