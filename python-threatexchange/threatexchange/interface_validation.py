# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
A way to connect all the key interfaces of the library.

This is entirely optional, and you can always use the classes directly
without any trouble, but you may find some of the validation methods
useful, especially if you are relying on the various .get_name() functions
as storage keys, since there are helpers here for asserting they are
all unique.

Since matching may need to look up context from the original fetching,
this is all the parts needed to get you there.

You don't need to do it this way, but it does make it clear which
fetching, matching, and other capabilities you are supporting.
"""

import typing as t
from dataclasses import dataclass

from threatexchange.content_type.content_base import ContentType
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.exchanges.signal_exchange_api import (
    TSignalExchangeAPICls,
)
from threatexchange.exchanges.collab_config import CollaborationConfigStoreBase


class SignalTypeMapping:
    def __init__(
        self,
        content_types: t.List[t.Type[ContentType]],
        signal_types: t.List[t.Type[SignalType]],
    ):
        _validate_content_and_signal(content_types, signal_types)

        self.content_by_name = {c.get_name(): c for c in content_types}
        self.signal_type_by_name = {s.get_name(): s for s in signal_types}
        self.signal_type_by_content: t.Dict[
            t.Type[ContentType], t.List[t.Type[SignalType]]
        ] = {c: [] for c in content_types}
        for signal_type in signal_types:
            for content_type in signal_type.get_content_types():
                self.signal_type_by_content[content_type].append(signal_type)

    def get_supported_signal_types_for_content(
        self, content: t.Type[ContentType]
    ) -> t.List[t.Type[SignalType]]:
        # TODO - consider storing by tuple instead of defending against accidental
        #        mutation by callers
        return list(self.signal_type_by_content.get(content, ()))


class SignalExchangeAPIMapping:
    def __init__(self, apis: t.Sequence[TSignalExchangeAPICls]) -> None:
        _validate_signal_apis(apis)
        self.api_by_name = {f.get_name(): f for f in apis}


@dataclass
class FunctionalityMapping:
    """
    All of key fetch, hash, match interfaces combined.

    Since matching may need to look up context from the original fetching,
    this container provides all the interfaces needed to get you there.
    """

    signal_and_content: SignalTypeMapping
    exchange: SignalExchangeAPIMapping
    collabs: CollaborationConfigStoreBase


def _validate_signal_apis(apis: t.Iterable[TSignalExchangeAPICls]):
    names = set()
    for a in apis:
        name = a.get_name()
        assert name not in names, f"Duplicate name in {a.__name__}s: '{name}'"
        names.add(name)


def _validate_content_types(content_types: t.List[t.Type[ContentType]]) -> None:
    names = set()
    for c in content_types:
        name = c.get_name()
        assert name not in names, f"Duplicate name in {ContentType.__name__}s: '{name}'"
        names.add(name)


def _validate_signal_types(signal_types: t.List[t.Type[SignalType]]):
    names = set()
    for s in signal_types:
        name = s.get_name()
        assert name not in names, f"Duplicate name in {SignalType.__name__}s: '{name}'"
        names.add(name)


def _validate_content_and_signal(
    content_types: t.List[t.Type[ContentType]],
    signal_types: t.List[t.Type[SignalType]],
) -> None:
    _validate_content_types(content_types)
    _validate_signal_types(signal_types)
    supported_ct = set(content_types)
    for signal_type in signal_types:
        supported = any(c in supported_ct for c in signal_type.get_content_types())
        assert supported, f"No signal types for content type: {signal_type.get_name()}"
