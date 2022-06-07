# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

from collections import defaultdict
from dataclasses import dataclass
import typing as t

from threatexchange.fetcher.collab_config import (
    CollaborationConfigBase,
    CollaborationConfigWithDefaults,
)
from threatexchange.fetcher.fetch_api import (
    TSignalExchangeAPI,
)
from threatexchange.fetcher.fetch_state import (
    FetchCheckpointBase,
    SignalOpinion,
    SignalOpinionCategory,
)

from threatexchange.fetcher.simple.state import (
    FetchDeltaWithUpdateStream,
    SimpleFetchDelta,
    SimpleFetchedSignalMetadata,
    SimpleFetchedStateStore,
    T_FetchDelta,
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


@dataclass
class FakeFetchDelta(
    FetchDeltaWithUpdateStream[
        FakeCheckpoint, SimpleFetchedSignalMetadata, int, FakeUpdateRecord
    ]
):
    """
    Simulates an update types that uses per-owner opinions with an int ID.

    Its easiest to store as record_id => opinion, but then we need to
    map it to hash => merged_opinions
    """

    def get_for_signal_type(
        self, signal_type: t.Type[SignalType]
    ) -> t.Dict[str, SimpleFetchedSignalMetadata]:
        remapped: t.DefaultDict[str, t.DefaultDict[int, t.Set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )
        if signal_type == VideoMD5Signal:
            for _k, update in self.update_record.items():
                if update is not None:
                    remapped[update.md5][update.owner].add(update.tag)

        return {
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


class FakeSimpleFetchDelta(
    SimpleFetchDelta[FakeCheckpoint, SimpleFetchedSignalMetadata]
):
    pass


class FakeFetchStore(SimpleFetchedStateStore):
    def __init__(
        self,
    ) -> None:
        super().__init__(TSignalExchangeAPI)  # type: ignore
        self._fake_storage: t.Dict[str, T_FetchDelta] = {}

    def clear(self, collab: CollaborationConfigBase) -> None:
        self._fake_storage.pop(collab.name, None)

    def _read_state(
        self,
        collab_name: str,
    ) -> t.Optional[T_FetchDelta]:
        return self._fake_storage.get(collab_name)

    def _write_state(self, collab_name: str, delta: T_FetchDelta) -> None:
        self._fake_storage[collab_name] = delta


def md5(n):
    return f"{n:032x}"


def test_test_impls():
    """
    Since we're faking these interfaces, lets make sure they behave as expected
    """
    store = FakeFetchStore()
    config = CollaborationConfigWithDefaults("fake_collab_name")

    assert store.get_checkpoint(config) == None
    assert store.get_for_signal_type([config], VideoMD5Signal) == {}

    checkpoint = FakeCheckpoint(100)

    md5 = "0" * 32
    delta = FakeFetchDelta({1: FakeUpdateRecord(1, "tag", md5)}, checkpoint)

    record = SimpleFetchedSignalMetadata(
        [SignalOpinion(1, SignalOpinionCategory.WORTH_INVESTIGATING, {"tag"})]
    )

    assert delta.next_checkpoint() == checkpoint
    assert delta.record_count() == 1

    assert delta.get_for_signal_type(VideoMD5Signal) == {md5: record}
    assert delta.get_for_signal_type(RawTextSignal) == {}


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

    store = FakeFetchStore()
    collab = CollaborationConfigWithDefaults("fake_collab_name")
    checkpoint = FakeCheckpoint(100)

    # If we appy updates all at once, we expect just the final state
    # Note - dict(updates) work because our merge behavior is replace
    delta = FakeFetchDelta(dict(updates), checkpoint)
    assert delta.get_for_signal_type(VideoMD5Signal) == expected_states[-1]

    store.merge(collab, delta)
    store.flush()
    assert store.get_for_signal_type([collab], VideoMD5Signal) == {
        collab.name: expected_states[-1]
    }

    store = FakeFetchStore()
    # If we appy updates 1-by-1 we expect all the end states
    for i, update in enumerate(updates):
        checkpoint = FakeCheckpoint(100 + i)
        delta = FakeFetchDelta(dict([update]), checkpoint)
        store.merge(collab, delta)
        store.flush()
        assert store.get_for_signal_type([collab], VideoMD5Signal) == {
            collab.name: expected_states[i]
        }, f"Update {i}"
        assert store.get_checkpoint(collab) == checkpoint


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

    store = FakeFetchStore()
    collab = CollaborationConfigWithDefaults("fake_collab_name")
    checkpoint = FakeCheckpoint(100)

    # If we appy updates all at once, we expect just the final state
    # Note - dict(updates) work because our merge behavior is replace
    delta = FakeSimpleFetchDelta(dict(updates), checkpoint)
    assert delta.get_for_signal_type(VideoMD5Signal) == expected_states[-1]

    store.merge(collab, delta)
    store.flush()
    assert store.get_for_signal_type([collab], VideoMD5Signal) == {
        collab.name: expected_states[-1]
    }

    store = FakeFetchStore()
    # If we appy updates 1-by-1 we expect all the end states
    for i, update in enumerate(updates):
        checkpoint = FakeCheckpoint(100 + i)
        delta = FakeSimpleFetchDelta(dict([update]), checkpoint)
        store.merge(collab, delta)
        store.flush()
        assert store.get_for_signal_type([collab], VideoMD5Signal) == {
            collab.name: expected_states[i]
        }, f"Update {i}"
        assert store.get_checkpoint(collab) == checkpoint
