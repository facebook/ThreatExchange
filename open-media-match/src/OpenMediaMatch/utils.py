# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Accessors for various "global" resources, usually cached by request lifetime

I can't tell if these should just be in app.py, so I'm sticking it here for now,
since one advantage of putting these in functions is we can type the output.
"""

import functools
import typing as t

from flask import g, abort, request
from werkzeug.exceptions import HTTPException

TArg = t.TypeVar("TArg", bool, int, float)
TFn = t.TypeVar("TFn", bound=t.Callable[..., t.Any])


def abort_to_json(fn: TFn) -> TFn:
    """
    Wrap json endpoints to turn abort("message", code) to json

    @bp.route("/function")

    def function():
      if thing:
        abort(400, "thing missin")

    will return
        HTTP/1.1 400 BAD_REQUEST
        Content-Type: application/json

        {
            "message": "thing missin"
        }
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwds):
        try:
            return fn(*args, **kwds)
        except HTTPException as e:
            return {"message": e.description}, e.code

    return t.cast(TFn, wrapper)


def require_request_param(name: str) -> str:
    """
    Wrapper around a required request parameter.

    aborts with 400 if it's missing.
    """
    ret = request.args.get(name)
    if ret is None:
        abort(400, f"{name} is required")
    return ret


def require_json_param(name: str) -> str:
    """
    Wrapper around a required POST json parameter.

    aborts with 400 if it's missing.
    """
    val = request.get_json().get(name)
    if val is None:
        abort(400, f"{name} is required")
    return val


def str_to_bool(s: str) -> bool:
    if s.lower() in ("true", "1"):
        return True
    if s.lower() in ("false", "0"):
        return False
    abort(400, "invalid boolean parameter - prefer true/false")


def str_to_type(s: str, t: t.Type[TArg]) -> TArg:
    if t == bool:
        return str_to_bool(s)
    try:
        return t(s)
    except ValueError:
        abort(400, f"Invalid {t.__name__}: '{s}'")
