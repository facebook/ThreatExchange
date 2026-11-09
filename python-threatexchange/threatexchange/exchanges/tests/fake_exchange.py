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
    Records keyed by int id rather than by signal, roughly like NCMEC.

    Updates are Mapping[int, Optional[FakeIdRecord]]:
    * Key: the record id.
    * Value: the full current state of that record. It replaces whatever
      was stored for that id; there are no partial updates.
    * Delete: either `None` or a `FakeIdRecord(deleted=True)` tombstone
      (the NCMEC style). Both remove the record.

    Signals come from the record's fields: `md5` -> VideoMD5Signal and
    `pdq` -> PdqSignal. A record with neither is still stored, but yields
    no signals. naive_convert_to_signal_type() merges every record with the
    same signal into one INVESTIGATION_SEED opinion per `owner`, unioning
    their tags.

    Fetches are scripted through the constructor: each mapping in `fetches`
    is one FetchDelta from fetch_iter(), with checkpoints
    FakeCheckpoint(100), FakeCheckpoint(200), ... The checkpoint passed to
    fetch_iter() is ignored, so every call replays all the fetches.
    for_collab() returns an instance with no fetches.

    Example:

        md5 = "0" * 32
        api = FakeIdKeyedAPI(
            [
                # First fetch: two owners flag the same md5
                {
                    1: FakeIdRecord(owner=1, tags=["a"], md5=md5),
                    2: FakeIdRecord(owner=2, tags=["b"], md5=md5),
                },
                # Second fetch: record 1 is updated, record 2 is deleted
                {
                    1: FakeIdRecord(owner=1, tags=["c"], md5=md5),
                    2: FakeIdRecord(deleted=True),
                },
            ]
        )
        collab = FakeIdKeyedAPI.make_collab()
        first, second = api.fetch_iter([], None)
        assert first.checkpoint == FakeCheckpoint(100)
        assert FakeIdKeyedAPI.naive_convert_to_signal_type(
            [VideoMD5Signal], collab, first.updates
        ) == {
            VideoMD5Signal: {
                md5: FakeSignalMetadata(
                    [
                        SignalOpinionWithOwner(
                            SignalOpinionCategory.INVESTIGATION_SEED, {"a"}, 1
                        ),
                        SignalOpinionWithOwner(
                            SignalOpinionCategory.INVESTIGATION_SEED, {"b"}, 2
                        ),
                    ]
                )
            }
        }

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
    Shortcut for typing converting API literals into the form storage expects
    e.g. DBMStore(exchange_types=...)
    """
    return t.cast(t.List[TSignalExchangeAPICls], list(apis))
