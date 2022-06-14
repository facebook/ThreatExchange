# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

from collections import defaultdict
from dataclasses import dataclass
import typing as t

from threatexchange.fetcher.collab_config import (
    CollaborationConfigBase,
    CollaborationConfigWithDefaults,
)
from threatexchange.fetcher.fetch_api import (
    SignalExchangeAPIWithKeyedUpdates,
    SignalExchangeAPIWithSimpleUpdates,
)
from threatexchange.fetcher.fetch_state import (
    FetchCheckpointBase,
    FetchDelta,
    FetchDeltaTyped,
    SignalOpinion,
    SignalOpinionCategory,
)

from threatexchange.fetcher.simple.state import (
    SimpleFetchedSignalMetadata,
    SimpleFetchedStateStore,
)
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.raw_text import RawTextSignal
from threatexchange.signal_type.signal_base import SignalType


@dataclass
class FakeCheckpoint(FetchCheckpointBase):
    update_time: int


@dataclass
class FakeUpdateRecord:
    owner: int
    tag: str
    md5: str


OpinionRecord = t.Dict[int, t.Optional[FakeUpdateRecord]]
OpinionDelta = FetchDelta[OpinionRecord, FetchCheckpointBase]

K = t.TypeVar("K")
V = t.TypeVar("V")


class _FakeAPIMixin(t.Generic[K, V]):
    """
    Simulates an update types that uses per-owner opinions with an int ID.

    Its easiest to store as record_id => opinion, but then we need to
    map it to hash => merged_opinions
    """

    def __init__(self, fetches: t.Sequence[t.Dict[K, t.Optional[V]]]) -> None:
        self.fetches = fetches

    @classmethod
    def get_fake_collab_config(cls) -> CollaborationConfigBase:
        return CollaborationConfigWithDefaults("Test State", cls.get_name())  # type: ignore

    def fetch_iter(
        self,
        supported_signal_types: t.Sequence[t.Type[SignalType]],
        collab: CollaborationConfigBase,
        # None if fetching for the first time,
        # otherwise the previous FetchDelta returned
        checkpoint: t.Optional[FakeCheckpoint],
    ) -> t.Iterator[FetchDelta[t.Dict[K, t.Optional[V]], FakeCheckpoint]]:
        for i, update in enumerate(self.fetches):
            yield FetchDelta(update, FakeCheckpoint((i + 1) * 100))


class FakePerOwnerOpinionAPI(
    _FakeAPIMixin[int, FakeUpdateRecord],
    SignalExchangeAPIWithKeyedUpdates[
        CollaborationConfigBase,
        FakeCheckpoint,
        SimpleFetchedSignalMetadata,
        int,
        FakeUpdateRecord,
    ],
):
    @classmethod
    def naive_convert_to_signal_type(
        cls,
        signal_types: t.Sequence[t.Type[SignalType]],
        fetched: t.Dict[int, t.Optional[FakeUpdateRecord]],
    ) -> t.Dict[t.Type[SignalType], t.Dict[str, SimpleFetchedSignalMetadata]]:
        if VideoMD5Signal not in signal_types:
            return {}

        remapped: t.DefaultDict[str, t.DefaultDict[int, t.Set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )
        for update in fetched.values():
            if update is not None:
                remapped[update.md5][update.owner].add(update.tag)

        return {
            VideoMD5Signal: {
                h: SimpleFetchedSignalMetadata(
                    [
                        SignalOpinion(
                            owner=owner,
                            category=SignalOpinionCategory.WORTH_INVESTIGATING,
                            tags=tags,
                        )
                        for owner, tags in tags_per_owner.items()
                    ]
                )
                for h, tags_per_owner in remapped.items()
            }
        }


class FakeNoConversionAPI(
    _FakeAPIMixin[t.Tuple[str, str], SimpleFetchedSignalMetadata],
    SignalExchangeAPIWithSimpleUpdates[
        CollaborationConfigBase,
        FakeCheckpoint,
        SimpleFetchedSignalMetadata,
    ],
):
    pass


class FakeFetchStore(SimpleFetchedStateStore):
    def __init__(self, api_cls) -> None:
        super().__init__(api_cls)
        self._fake_storage: t.Dict[str, FetchDeltaTyped] = {}

    def clear(self, collab: CollaborationConfigBase) -> None:
        self._fake_storage.pop(collab.name, None)

    def _read_state(
        self,
        collab_name: str,
    ) -> t.Optional[FetchDeltaTyped]:
        return self._fake_storage.get(collab_name)

    def _write_state(self, collab_name: str, delta: FetchDeltaTyped) -> None:
        self._fake_storage[collab_name] = delta


def md5(n):
    return f"{n:032x}"


def test_test_impls():
    """
    Since we're faking these interfaces, lets make sure they behave as expected
    """
    store = FakeFetchStore(FakePerOwnerOpinionAPI)
    config = FakePerOwnerOpinionAPI.get_fake_collab_config()

    assert store.get_checkpoint(config) == None
    assert store.get_for_signal_type([config], VideoMD5Signal) == {}

    md5 = "0" * 32

    api = FakePerOwnerOpinionAPI([{1: FakeUpdateRecord(1, "tag", md5)}])
    deltas = list(api.fetch_iter([], config, None))
    assert len(deltas) == 1
    delta = deltas[0]
    assert delta.checkpoint == FakeCheckpoint(100)

    record = SimpleFetchedSignalMetadata(
        [SignalOpinion(1, SignalOpinionCategory.WORTH_INVESTIGATING, {"tag"})]
    )

    assert FakePerOwnerOpinionAPI.naive_convert_to_signal_type(
        [VideoMD5Signal], delta.updates
    ) == {VideoMD5Signal: {md5: record}}
    assert (
        FakePerOwnerOpinionAPI.naive_convert_to_signal_type(
            [RawTextSignal], delta.updates
        )
        == {}
    )

    store.merge(config, delta)
    store.flush()
    assert store.get_for_signal_type([config], RawTextSignal) == {}
    assert store.get_for_signal_type([config], VideoMD5Signal) == {
        config.name: {md5: record}
    }


def test_update_stream_delta():
    t1 = "tag"
    t2 = "other"
    t3 = "foo"

    updates = [
        # Hash 1
        (0, FakeUpdateRecord(1, t1, md5(1))),
        (1, FakeUpdateRecord(1, t2, md5(1))),  # Combine
        (2, FakeUpdateRecord(2, t3, md5(1))),  # Combine
        # Hash 2
        (3, FakeUpdateRecord(3, t1, md5(2))),
        (3, FakeUpdateRecord(3, t2, md5(2))),  # Replace
        # Hash 1 again
        (0, FakeUpdateRecord(1, t3, md5(1))),
        (4, FakeUpdateRecord(3, t3, md5(1))),
        # Deletes
        (0, None),  # Delete a record
        (1, None),
        (2, None),
        (4, None),  # Completely remove hash
    ]

    h1_full = SimpleFetchedSignalMetadata(
        [
            SignalOpinion(1, SignalOpinionCategory.WORTH_INVESTIGATING, {t1, t2}),
            SignalOpinion(2, SignalOpinionCategory.WORTH_INVESTIGATING, {t3}),
        ]
    )
    h2_full = SimpleFetchedSignalMetadata(
        [
            SignalOpinion(3, SignalOpinionCategory.WORTH_INVESTIGATING, {t2}),
        ]
    )

    expected_states = [
        # Hash 1
        {
            md5(1): SimpleFetchedSignalMetadata(
                [SignalOpinion(1, SignalOpinionCategory.WORTH_INVESTIGATING, {t1})]
            )
        },
        {
            md5(1): SimpleFetchedSignalMetadata(
                [SignalOpinion(1, SignalOpinionCategory.WORTH_INVESTIGATING, {t1, t2})]
            )
        },
        {md5(1): h1_full},
        # Hash 2
        {
            md5(1): h1_full,
            md5(2): SimpleFetchedSignalMetadata(
                [
                    SignalOpinion(3, SignalOpinionCategory.WORTH_INVESTIGATING, {t1}),
                ]
            ),
        },
        {
            md5(1): h1_full,
            md5(2): h2_full,
        },
        # Hash 1 again
        {
            md5(1): SimpleFetchedSignalMetadata(
                [
                    SignalOpinion(
                        1, SignalOpinionCategory.WORTH_INVESTIGATING, {t2, t3}
                    ),
                    SignalOpinion(2, SignalOpinionCategory.WORTH_INVESTIGATING, {t3}),
                ]
            ),
            md5(2): h2_full,
        },
        {
            md5(1): SimpleFetchedSignalMetadata(
                [
                    SignalOpinion(
                        1, SignalOpinionCategory.WORTH_INVESTIGATING, {t2, t3}
                    ),
                    SignalOpinion(2, SignalOpinionCategory.WORTH_INVESTIGATING, {t3}),
                    SignalOpinion(3, SignalOpinionCategory.WORTH_INVESTIGATING, {t3}),
                ]
            ),
            md5(2): h2_full,
        },
        # Deletes
        {
            md5(1): SimpleFetchedSignalMetadata(
                [
                    SignalOpinion(1, SignalOpinionCategory.WORTH_INVESTIGATING, {t2}),
                    SignalOpinion(2, SignalOpinionCategory.WORTH_INVESTIGATING, {t3}),
                    SignalOpinion(3, SignalOpinionCategory.WORTH_INVESTIGATING, {t3}),
                ]
            ),
            md5(2): h2_full,
        },
        {
            md5(1): SimpleFetchedSignalMetadata(
                [
                    SignalOpinion(2, SignalOpinionCategory.WORTH_INVESTIGATING, {t3}),
                    SignalOpinion(3, SignalOpinionCategory.WORTH_INVESTIGATING, {t3}),
                ]
            ),
            md5(2): h2_full,
        },
        {
            md5(1): SimpleFetchedSignalMetadata(
                [
                    SignalOpinion(3, SignalOpinionCategory.WORTH_INVESTIGATING, {t3}),
                ]
            ),
            md5(2): h2_full,
        },
        {md5(2): h2_full},
    ]

    store = FakeFetchStore(FakePerOwnerOpinionAPI)
    collab = FakePerOwnerOpinionAPI.get_fake_collab_config()

    # Note - dict(updates) work because our merge behavior is replace
    api = FakePerOwnerOpinionAPI([dict(updates)])

    # If we appy updates all at once, we expect just the final state
    delta = next(api.fetch_iter([], collab, None))

    store.merge(collab, delta)
    store.flush()
    assert store.get_for_signal_type([collab], VideoMD5Signal) == {
        collab.name: expected_states[-1]
    }

    store = FakeFetchStore(FakePerOwnerOpinionAPI)
    # If we appy updates 1-by-1 we expect all the end states
    api = FakePerOwnerOpinionAPI([dict([t]) for t in updates])
    for i, delta in enumerate(api.fetch_iter([], collab, None)):
        store.merge(collab, delta)
        store.flush()
        assert store.get_for_signal_type([collab], VideoMD5Signal) == {
            collab.name: expected_states[i]
        }, f"Update {i}"
        assert store.get_checkpoint(collab) == delta.checkpoint


def test_simple_update_delta():
    def key(n):
        return (VideoMD5Signal.get_name(), md5(n))

    t1 = "tag"
    t2 = "other"
    t3 = "foo"

    h1_full = SimpleFetchedSignalMetadata(
        [
            SignalOpinion(1, SignalOpinionCategory.WORTH_INVESTIGATING, {t1, t2}),
            SignalOpinion(2, SignalOpinionCategory.WORTH_INVESTIGATING, {t3}),
        ]
    )
    h2_full = SimpleFetchedSignalMetadata(
        [
            SignalOpinion(3, SignalOpinionCategory.WORTH_INVESTIGATING, {t2}),
        ]
    )

    updates = [
        # Hash 1
        (
            key(1),
            SimpleFetchedSignalMetadata(
                [SignalOpinion(1, SignalOpinionCategory.WORTH_INVESTIGATING, {t1})]
            ),
        ),
        (
            key(1),
            SimpleFetchedSignalMetadata(
                [SignalOpinion(1, SignalOpinionCategory.WORTH_INVESTIGATING, {t1, t2})]
            ),
        ),
        (key(1), h1_full),
        # Hash 2
        (
            key(2),
            h2_full,
        ),
        # Hash 1 again
        (
            key(1),
            SimpleFetchedSignalMetadata(
                [
                    SignalOpinion(
                        1, SignalOpinionCategory.WORTH_INVESTIGATING, {t2, t3}
                    ),
                    SignalOpinion(2, SignalOpinionCategory.WORTH_INVESTIGATING, {t3}),
                ]
            ),
        ),
        # Delete
        (key(1), None),
    ]

    expected_states = [
        # Hash 1
        {
            md5(1): SimpleFetchedSignalMetadata(
                [SignalOpinion(1, SignalOpinionCategory.WORTH_INVESTIGATING, {t1})]
            )
        },
        {
            md5(1): SimpleFetchedSignalMetadata(
                [SignalOpinion(1, SignalOpinionCategory.WORTH_INVESTIGATING, {t1, t2})]
            )
        },
        {md5(1): h1_full},
        # Hash 2
        {
            md5(1): h1_full,
            md5(2): h2_full,
        },
        # Hash 1 again
        {
            md5(1): SimpleFetchedSignalMetadata(
                [
                    SignalOpinion(
                        1, SignalOpinionCategory.WORTH_INVESTIGATING, {t2, t3}
                    ),
                    SignalOpinion(2, SignalOpinionCategory.WORTH_INVESTIGATING, {t3}),
                ]
            ),
            md5(2): h2_full,
        },
        # Delete
        {md5(2): h2_full},
    ]

    store = FakeFetchStore(FakeNoConversionAPI)
    collab = FakeNoConversionAPI.get_fake_collab_config()

    # Note - dict(updates) work because our merge behavior is replace
    api = FakeNoConversionAPI([dict(updates)])
    # If we appy updates all at once, we expect just the final state
    delta = next(api.fetch_iter([], collab, None))
    store.merge(collab, delta)
    store.flush()
    assert store.get_for_signal_type([collab], VideoMD5Signal) == {
        collab.name: expected_states[-1]
    }

    store = FakeFetchStore(FakeNoConversionAPI)
    # If we appy updates 1-by-1 we expect all the end states
    api = FakeNoConversionAPI([dict([t]) for t in updates])
    for i, delta in enumerate(api.fetch_iter([], collab, None)):
        store.merge(collab, delta)
        store.flush()
        assert store.get_for_signal_type([collab], VideoMD5Signal) == {
            collab.name: expected_states[i]
        }, f"Update {i}"
        assert store.get_checkpoint(collab) == delta.checkpoint
