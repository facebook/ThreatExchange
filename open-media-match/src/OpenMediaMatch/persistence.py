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

from flask import g, current_app

from OpenMediaMatch.storage.interface import IUnifiedStore
from OpenMediaMatch.storage.default import DefaultOMMStore

from threatexchange.signal_type.signal_base import SignalType
from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal

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


def get_installed_signal_types() -> list[t.Type[SignalType]]:
    if "signal_types" not in g:
        signal_types = current_app.config.get("SIGNAL_TYPES")
        if signal_types is not None:
            assert isinstance(signal_types, list)
            for element in signal_types:
                assert issubclass(element, SignalType)
            g.signal_types = signal_types
        else:
            g.signal_types = [PdqSignal, VideoMD5Signal]

        assert len(g.signal_types) == len(
            set([s.get_name() for s in g.signal_types])
        ), "All signal must have unique names"
    return g.signal_types
