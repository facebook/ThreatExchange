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

from OpenMediaMatch.storage.interface import IUnifiedStore
from OpenMediaMatch.storage.default import DefaultOMMStore

T = t.TypeVar("T", bound=t.Callable[..., t.Any])


def get_storage() -> IUnifiedStore:
    """
    Get the storage object, which is just a wrapper around the real storage.
    """
    if "storage" not in g:
        # dougneal, you'll need to eventually add constructor arguments
        # for this to pass in the postgres/database object. We're just
        # hiding flask bits from pytx bits
        g.storage = DefaultOMMStore()
    return g.storage


def abort_to_json(fn: T) -> T:
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

    return t.cast(T, wrapper)


def require_request_param(name: str) -> str:
    """
    Wrapper around a required request parameter.

    aborts with 400 if it's missing.
    """
    ret = request.args.get(name)
    if ret is None:
        abort(400, f"{name} is required")
    return ret
