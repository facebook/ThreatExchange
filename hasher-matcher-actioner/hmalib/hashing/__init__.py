# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import typing as t
from dataclasses import dataclass

from threatexchange.content_type.content_base import ContentType
from threatexchange.signal_type.signal_base import SignalType, BytesHasher


@dataclass
class SignalValue:
    signal_type: SignalType
    signal_value: str


class Hasher:
    def __init__(
        self,
        supported_content_types: t.List[t.Type[ContentType]],
        supported_signal_types: t.List[t.Type[SignalType]],
    ):
        self.supported_content_types = supported_content_types

        # Not enforced in typing because python does not yet have t.Intersect,
        # but all supported_signal_types must also implement BytesHasher
        assert all([issubclass(t, BytesHasher) for t in supported_signal_types])

        self.supported_signal_types = supported_signal_types

    def supports(self, content_type: t.Type[ContentType]) -> bool:
        """
        Can this hasher produce signals for content of `content_type`?
        """
        return content_type in self.supported_content_types

    def get_hashes(
        self, content_type: t.Type[ContentType], bytes_: bytes
    ) -> t.Generator[SignalValue, None, None]:
        for signal_type in content_type.get_signal_types():
            if signal_type in self.supported_signal_types and issubclass(
                signal_type, BytesHasher
            ):
                yield SignalValue(signal_type, signal_type.hash_from_bytes(bytes_))
