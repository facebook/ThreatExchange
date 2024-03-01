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

from flask import current_app

from OpenMediaMatch.storage.interface import IUnifiedStore


def get_storage() -> IUnifiedStore:
    """
    Get the storage interface for the current app flask instance

    Holdover from earlier development, maybe remove someday.
    """
    return t.cast(IUnifiedStore, current_app.config["STORAGE_IFACE_INSTANCE"])
