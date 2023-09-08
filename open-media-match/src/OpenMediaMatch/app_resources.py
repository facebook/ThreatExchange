# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Accessors for various "global" resources, usually cached by request lifetime

I can't tell if these should just be in app.py, so I'm sticking it here for now,
since one advantage of putting these in functions is we can type the output.
"""

from flask import g

from OpenMediaMatch.storage.interface import IUnifiedStore
from OpenMediaMatch.storage.default import DefaultOMMStore


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
