# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
A shim around persistence layer of the OMM instance.

This includes relational data, blob storage, etc.

It doesn't include logging (just use current_app.logger).

We haven't made all of the hard decisions on the storage yet, and
think future deployers may change their mind about which backends to
use. We know we are going to have more than relational data, so
SQLAlchemy isn't going to be enough. Thus an even more abstract
accessor. 


"""

import typing as t

from flask import g

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
