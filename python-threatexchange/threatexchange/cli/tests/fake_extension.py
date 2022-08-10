# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

from dataclasses import dataclass, field
import enum
import pathlib
import typing as t
from threatexchange.exchanges.collab_config import (
    CollaborationConfigBase,
    CollaborationConfigWithDefaults,
)
from threatexchange.exchanges.fetch_state import (
    FetchCheckpointBase,
    FetchDelta,
    FetchedSignalMetadata,
)

from threatexchange.extensions.manifest import ThreatExchangeExtensionManifest
from threatexchange.signal_type.signal_base import (
    FileHasher,
    SignalComparisonResult,
    SignalType,
    TrivialSignalTypeIndex,
)
from threatexchange.content_type.content_base import ContentType
from threatexchange.exchanges.signal_exchange_api import SignalExchangeAPI


class FakeContent(ContentType):
    pass


class FakeEnum(enum.Enum):
    OPTION_A = "a"
    OPTION_B = "b"
    CamelCase = "camels"
    lower_under = "under score"


@dataclass
class _FakeCollabConfigRequiredFields:
    an_int: int = field(metadata={"help": "Demonstrate int"})
    a_str: str = field(metadata={"help": "Demonstrate str"})
    a_list: t.List[str] = field(metadata={"help": "Demonstrate list"})
    a_set: t.Set[int] = field(metadata={"help": "Demonstrate set"})
    an_enum: FakeEnum = field(metadata={"help": "Demonstrate enum"})


@dataclass
class FakeCollabConfig(
    CollaborationConfigWithDefaults, _FakeCollabConfigRequiredFields
):
    optional: t.Optional[float] = field(
        default=None, metadata={"help": "Demonstrate optional float"}
    )


class FakeSignal(SignalType, FileHasher):
    @classmethod
    def get_content_types(cls) -> t.List[t.Type[ContentType]]:
        """Which content types this Signal applies to (usually just one)"""
        return [FakeContent]

    @classmethod
    def get_index_cls(cls) -> t.Type[TrivialSignalTypeIndex]:
        return TrivialSignalTypeIndex

    @classmethod
    def hash_from_file(cls, file: pathlib.Path) -> str:
        return "fake"  # A perfect hashing algorithm

    @classmethod
    def get_examples(cls) -> t.List[str]:
        return ["fake", "not fake"]


class FakeSignalExchange(
    SignalExchangeAPI[
        FakeCollabConfig, FetchCheckpointBase, FetchedSignalMetadata, str, str
    ]
):
    @classmethod
    def get_config_cls(cls) -> t.Type[FakeCollabConfig]:
        return FakeCollabConfig

    @classmethod
    def naive_convert_to_signal_type(
        cls,
        signal_types: t.Sequence[t.Type[SignalType]],
        collab: FakeCollabConfig,
        fetched: t.Mapping[str, str],
    ) -> t.Dict[t.Type[SignalType], t.Dict[str, FetchedSignalMetadata]]:
        return {}

    def fetch_iter(
        self,
        supported_signal_types: t.Sequence[t.Type[SignalType]],
        # None if fetching for the first time,
        # otherwise the previous FetchDelta returned
        checkpoint: t.Optional[FetchCheckpointBase],
    ) -> t.Iterator[FetchDelta[str, str, FetchCheckpointBase]]:
        return
        yield  # how to write an empty generator


TX_MANIFEST = ThreatExchangeExtensionManifest(
    signal_types=(FakeSignal,),
    content_types=(FakeContent,),
    apis=(FakeSignalExchange,),
)
