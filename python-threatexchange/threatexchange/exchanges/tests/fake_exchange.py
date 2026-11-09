# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Fake SignalExchangeAPI implementations for tests.

Use these instead of writing a new fake exchange in each test file.

* FakeSimpleUpdatesAPI: records keyed by (signal_type, signal), like
  StaticSampleSignalExchangeAPI or StopNCII.
* FakeIdKeyedAPI: records keyed by an int id, each carrying an owner,
  tags and signals, with tombstone deletes, like NCMEC.

Fetch results are scripted: pass the list of updates to the constructor,
and fetch_iter() yields one FetchDelta per entry.
"""

from collections import defaultdict
from dataclasses import dataclass, field
import typing as t

from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.exchanges.fetch_state import (
    FetchCheckpointBase,
    FetchDelta,
    FetchedSignalMetadata,
    SignalOpinion,
    SignalOpinionCategory,
    TUpdateRecordKey as K,
)
from threatexchange.exchanges.signal_exchange_api import (
    SignalExchangeAPI,
    SignalExchangeAPIWithSimpleUpdates,
    TSignalExchangeAPICls,
)
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.signal_base import SignalType

V = t.TypeVar("V")
R = t.TypeVar("R", bound=FetchedSignalMetadata)


@dataclass
class FakeCheckpoint(FetchCheckpointBase):
    update_time: int = 0


@dataclass
class SignalOpinionWithOwner(SignalOpinion):
    owner_id: int
    is_mine: bool = field(init=False, default=False)


@dataclass
class FakeSignalMetadata(FetchedSignalMetadata):
    opinions: t.List[SignalOpinionWithOwner] = field(default_factory=list)

    def get_as_opinions(self) -> t.Sequence[SignalOpinionWithOwner]:
        return self.opinions


class FakeExchangeAPIBase(
    SignalExchangeAPI[CollaborationConfigBase, FakeCheckpoint, R, K, V]
):
    """
    Implements the boilerplate of SignalExchangeAPI, with scripted fetches.

    Each entry in `fetches` is yielded by fetch_iter() as one FetchDelta,
    with checkpoints FakeCheckpoint(100), FakeCheckpoint(200), ...
    """

    def __init__(self, fetches: t.Sequence[t.Mapping[K, t.Optional[V]]] = ()) -> None:
        self.fetches: t.Sequence[t.Mapping[K, t.Optional[V]]] = fetches

    @classmethod
    def for_collab(
        cls, collab: CollaborationConfigBase
    ) -> "FakeExchangeAPIBase[R, K, V]":
        return cls()

    @classmethod
    def make_collab(
        cls, name: str = "test_collab", enabled: bool = True
    ) -> CollaborationConfigBase:
        return CollaborationConfigBase(name=name, api=cls.get_name(), enabled=enabled)

    @staticmethod
    def get_config_cls() -> t.Type[CollaborationConfigBase]:
        return CollaborationConfigBase

    @staticmethod
    def get_checkpoint_cls() -> t.Type[FakeCheckpoint]:
        return FakeCheckpoint

    def fetch_iter(
        self,
        supported_signal_types: t.Sequence[t.Type[SignalType]],
        checkpoint: t.Optional[FakeCheckpoint],
    ) -> t.Iterator[FetchDelta[K, V, FakeCheckpoint]]:
        for i, update in enumerate(self.fetches):
            yield FetchDelta(dict(update), FakeCheckpoint((i + 1) * 100))


class FakeSimpleUpdatesAPI(
    FakeExchangeAPIBase[FakeSignalMetadata, t.Tuple[str, str], FakeSignalMetadata],
    SignalExchangeAPIWithSimpleUpdates[
        CollaborationConfigBase, FakeCheckpoint, FakeSignalMetadata
    ],
):
    """Records keyed by (signal_type name, signal)"""

    @classmethod
    def get_name(cls) -> str:
        return "fake_simple"

    @staticmethod
    def get_record_cls() -> t.Type[FakeSignalMetadata]:
        return FakeSignalMetadata


@dataclass
class FakeIdRecord(FakeSignalMetadata):
    """
    One record of FakeIdKeyedAPI, roughly an NCMEC entry.

    This is a FakeSignalMetadata so that get_record_cls() can return it:
    DBMStore stores the update values and reads them back with
    get_record_cls(), so the two need to be the same class.
    """

    owner: int = 0
    tags: t.List[str] = field(default_factory=list)
    md5: t.Optional[str] = None
    pdq: t.Optional[str] = None
    deleted: bool = False

    def signals(self) -> t.Dict[t.Type[SignalType], str]:
        ret: t.Dict[t.Type[SignalType], str] = {}
        if self.md5 is not None:
            ret[VideoMD5Signal] = self.md5
        if self.pdq is not None:
            ret[PdqSignal] = self.pdq
        return ret


class FakeIdKeyedAPI(FakeExchangeAPIBase[FakeSignalMetadata, int, FakeIdRecord]):
    """
    Records keyed by int id rather than by signal.

    A record with deleted=True is a tombstone that removes the record.
    Otherwise a new record replaces the old one. Converting to signals merges
    the records for the same signal into one opinion per owner.
    """

    @classmethod
    def get_name(cls) -> str:
        return "fake_id_keyed"

    @staticmethod
    def get_record_cls() -> t.Type[FakeIdRecord]:
        return FakeIdRecord

    @classmethod
    def fetch_value_merge(
        cls, old: t.Optional[FakeIdRecord], new: t.Optional[FakeIdRecord]
    ) -> t.Optional[FakeIdRecord]:
        if new is not None and new.deleted:
            return None
        return new

    @classmethod
    def naive_convert_to_signal_type(
        cls,
        signal_types: t.Sequence[t.Type[SignalType]],
        collab: CollaborationConfigBase,
        fetched: t.Mapping[int, t.Optional[FakeIdRecord]],
    ) -> t.Dict[t.Type[SignalType], t.Dict[str, FakeSignalMetadata]]:
        # signal type -> signal -> owner -> tags
        remapped: t.DefaultDict[
            t.Type[SignalType], t.DefaultDict[str, t.DefaultDict[int, t.Set[str]]]
        ] = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
        for record in fetched.values():
            if record is None or record.deleted:
                continue
            for st, signal in record.signals().items():
                if st in signal_types:
                    remapped[st][signal][record.owner].update(record.tags)
        return {
            st: {
                signal: FakeSignalMetadata(
                    [
                        SignalOpinionWithOwner(
                            owner_id=owner,
                            category=SignalOpinionCategory.INVESTIGATION_SEED,
                            tags=tags,
                        )
                        for owner, tags in tags_per_owner.items()
                    ]
                )
                for signal, tags_per_owner in by_signal.items()
            }
            for st, by_signal in remapped.items()
        }


def exchange_types(*apis: type) -> t.List[TSignalExchangeAPICls]:
    """
    A list of exchange classes, typed for DBMStore(exchange_types=...) and
    similar, without a `# type: ignore[list-item]` on every entry.
    """
    return t.cast(t.List[TSignalExchangeAPICls], list(apis))
