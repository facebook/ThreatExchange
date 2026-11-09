# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t

from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.exchanges.signal_exchange_api import TSignalExchangeAPICls
from threatexchange.exchanges.fetch_state import (
    FetchDeltaTyped,
    SignalOpinionCategory,
)

from threatexchange.exchanges.helpers import SimpleFetchedStateStore
from threatexchange.exchanges.tests.fake_exchange import (
    FakeCheckpoint,
    FakeIdKeyedAPI,
    FakeIdRecord,
    FakeSignalMetadata,
    FakeSimpleUpdatesAPI,
    SignalOpinionWithOwner,
)
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.raw_text import RawTextSignal


class FakeFetchStore(SimpleFetchedStateStore):
    def __init__(self, api_cls: TSignalExchangeAPICls) -> None:
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


def md5(n: int) -> str:
    return f"{n:032x}"


def test_test_impls():
    """
    Since we're faking these interfaces, lets make sure they behave as expected
    """
    store = FakeFetchStore(FakeIdKeyedAPI)
    config = FakeIdKeyedAPI.make_collab("Test State")

    assert store.get_checkpoint(config) == None
    assert store.get_for_signal_type([config], VideoMD5Signal) == {}

    md5 = "0" * 32

    api = FakeIdKeyedAPI([{1: FakeIdRecord(owner=1, tags=["tag"], md5=md5)}])
    deltas = list(api.fetch_iter([], None))
    assert len(deltas) == 1
    delta = deltas[0]
    assert delta.checkpoint == FakeCheckpoint(100)

    record = FakeSignalMetadata(
        [SignalOpinionWithOwner(SignalOpinionCategory.INVESTIGATION_SEED, {"tag"}, 1)]
    )

    assert FakeIdKeyedAPI.naive_convert_to_signal_type(
        [VideoMD5Signal], config, delta.updates
    ) == {VideoMD5Signal: {md5: record}}
    assert (
        FakeIdKeyedAPI.naive_convert_to_signal_type(
            [RawTextSignal], config, delta.updates
        )
        == {}
    )

    store.merge(config, delta)
    store.flush()
    assert store.get_for_signal_type([config], RawTextSignal) == {}
    assert store.get_for_signal_type([config], VideoMD5Signal) == {
        config.name: {md5: record}
    }


def test_update_stream_delta() -> None:
    t1 = "tag"
    t2 = "other"
    t3 = "foo"

    updates = [
        # Hash 1
        (0, FakeIdRecord(owner=1, tags=[t1], md5=md5(1))),
        (1, FakeIdRecord(owner=1, tags=[t2], md5=md5(1))),  # Combine
        (2, FakeIdRecord(owner=2, tags=[t3], md5=md5(1))),  # Combine
        # Hash 2
        (3, FakeIdRecord(owner=3, tags=[t1], md5=md5(2))),
        (3, FakeIdRecord(owner=3, tags=[t2], md5=md5(2))),  # Replace
        # Hash 1 again
        (0, FakeIdRecord(owner=1, tags=[t3], md5=md5(1))),
        (4, FakeIdRecord(owner=3, tags=[t3], md5=md5(1))),
        # Deletes
        (0, None),  # Delete a record
        (1, None),
        (2, None),
        (4, None),  # Completely remove hash
    ]

    h1_full = FakeSignalMetadata(
        [
            SignalOpinionWithOwner(
                SignalOpinionCategory.INVESTIGATION_SEED, {t1, t2}, 1
            ),
            SignalOpinionWithOwner(SignalOpinionCategory.INVESTIGATION_SEED, {t3}, 2),
        ]
    )
    h2_full = FakeSignalMetadata(
        [
            SignalOpinionWithOwner(SignalOpinionCategory.INVESTIGATION_SEED, {t2}, 3),
        ]
    )

    expected_states = [
        # Hash 1
        {
            md5(1): FakeSignalMetadata(
                [
                    SignalOpinionWithOwner(
                        SignalOpinionCategory.INVESTIGATION_SEED, {t1}, 1
                    )
                ]
            )
        },
        {
            md5(1): FakeSignalMetadata(
                [
                    SignalOpinionWithOwner(
                        SignalOpinionCategory.INVESTIGATION_SEED, {t1, t2}, 1
                    )
                ]
            )
        },
        {md5(1): h1_full},
        # Hash 2
        {
            md5(1): h1_full,
            md5(2): FakeSignalMetadata(
                [
                    SignalOpinionWithOwner(
                        SignalOpinionCategory.INVESTIGATION_SEED, {t1}, 3
                    ),
                ]
            ),
        },
        {
            md5(1): h1_full,
            md5(2): h2_full,
        },
        # Hash 1 again
        {
            md5(1): FakeSignalMetadata(
                [
                    SignalOpinionWithOwner(
                        SignalOpinionCategory.INVESTIGATION_SEED, {t2, t3}, 1
                    ),
                    SignalOpinionWithOwner(
                        SignalOpinionCategory.INVESTIGATION_SEED, {t3}, 2
                    ),
                ]
            ),
            md5(2): h2_full,
        },
        {
            md5(1): FakeSignalMetadata(
                [
                    SignalOpinionWithOwner(
                        SignalOpinionCategory.INVESTIGATION_SEED, {t2, t3}, 1
                    ),
                    SignalOpinionWithOwner(
                        SignalOpinionCategory.INVESTIGATION_SEED, {t3}, 2
                    ),
                    SignalOpinionWithOwner(
                        SignalOpinionCategory.INVESTIGATION_SEED, {t3}, 3
                    ),
                ]
            ),
            md5(2): h2_full,
        },
        # Deletes
        {
            md5(1): FakeSignalMetadata(
                [
                    SignalOpinionWithOwner(
                        SignalOpinionCategory.INVESTIGATION_SEED, {t2}, 1
                    ),
                    SignalOpinionWithOwner(
                        SignalOpinionCategory.INVESTIGATION_SEED, {t3}, 2
                    ),
                    SignalOpinionWithOwner(
                        SignalOpinionCategory.INVESTIGATION_SEED, {t3}, 3
                    ),
                ]
            ),
            md5(2): h2_full,
        },
        {
            md5(1): FakeSignalMetadata(
                [
                    SignalOpinionWithOwner(
                        SignalOpinionCategory.INVESTIGATION_SEED, {t3}, 2
                    ),
                    SignalOpinionWithOwner(
                        SignalOpinionCategory.INVESTIGATION_SEED, {t3}, 3
                    ),
                ]
            ),
            md5(2): h2_full,
        },
        {
            md5(1): FakeSignalMetadata(
                [
                    SignalOpinionWithOwner(
                        SignalOpinionCategory.INVESTIGATION_SEED, {t3}, 3
                    ),
                ]
            ),
            md5(2): h2_full,
        },
        {md5(2): h2_full},
    ]

    store = FakeFetchStore(t.cast(TSignalExchangeAPICls, FakeIdKeyedAPI))
    collab = FakeIdKeyedAPI.make_collab("Test State")

    # Note - dict(updates) work because our merge behavior is replace
    api = FakeIdKeyedAPI([dict(updates)])

    # If we appy updates all at once, we expect just the final state
    delta = next(api.fetch_iter([], None))

    store.merge(collab, delta)
    store.flush()
    assert store.get_for_signal_type([collab], VideoMD5Signal) == {
        collab.name: expected_states[-1]
    }

    store = FakeFetchStore(t.cast(TSignalExchangeAPICls, FakeIdKeyedAPI))
    # If we appy updates 1-by-1 we expect all the end states
    api = FakeIdKeyedAPI([dict([t]) for t in updates])
    for i, delta in enumerate(api.fetch_iter([], None)):
        store.merge(collab, delta)
        store.flush()
        assert store.get_for_signal_type([collab], VideoMD5Signal) == {
            collab.name: expected_states[i]
        }, f"Update {i}"
        assert store.get_checkpoint(collab) == delta.checkpoint


def test_simple_update_delta() -> None:
    def key(n: int) -> t.Tuple[str, str]:
        return VideoMD5Signal.get_name(), md5(n)

    t1 = "tag"
    t2 = "other"
    t3 = "foo"

    h1_full = FakeSignalMetadata(
        [
            SignalOpinionWithOwner(
                SignalOpinionCategory.INVESTIGATION_SEED, {t1, t2}, 1
            ),
            SignalOpinionWithOwner(SignalOpinionCategory.INVESTIGATION_SEED, {t3}, 2),
        ]
    )
    h2_full = FakeSignalMetadata(
        [
            SignalOpinionWithOwner(SignalOpinionCategory.INVESTIGATION_SEED, {t2}, 3),
        ]
    )

    updates = [
        # Hash 1
        (
            key(1),
            FakeSignalMetadata(
                [
                    SignalOpinionWithOwner(
                        SignalOpinionCategory.INVESTIGATION_SEED, {t1}, 1
                    )
                ]
            ),
        ),
        (
            key(1),
            FakeSignalMetadata(
                [
                    SignalOpinionWithOwner(
                        SignalOpinionCategory.INVESTIGATION_SEED, {t1, t2}, 1
                    )
                ]
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
            FakeSignalMetadata(
                [
                    SignalOpinionWithOwner(
                        SignalOpinionCategory.INVESTIGATION_SEED, {t2, t3}, 1
                    ),
                    SignalOpinionWithOwner(
                        SignalOpinionCategory.INVESTIGATION_SEED, {t3}, 2
                    ),
                ]
            ),
        ),
        # Delete
        (key(1), None),
    ]

    expected_states = [
        # Hash 1
        {
            md5(1): FakeSignalMetadata(
                [
                    SignalOpinionWithOwner(
                        SignalOpinionCategory.INVESTIGATION_SEED, {t1}, 1
                    )
                ]
            )
        },
        {
            md5(1): FakeSignalMetadata(
                [
                    SignalOpinionWithOwner(
                        SignalOpinionCategory.INVESTIGATION_SEED, {t1, t2}, 1
                    )
                ]
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
            md5(1): FakeSignalMetadata(
                [
                    SignalOpinionWithOwner(
                        SignalOpinionCategory.INVESTIGATION_SEED, {t2, t3}, 1
                    ),
                    SignalOpinionWithOwner(
                        SignalOpinionCategory.INVESTIGATION_SEED, {t3}, 2
                    ),
                ]
            ),
            md5(2): h2_full,
        },
        # Delete
        {md5(2): h2_full},
    ]

    store = FakeFetchStore(FakeSimpleUpdatesAPI)  # type: ignore[arg-type]
    collab = FakeSimpleUpdatesAPI.make_collab("Test State")

    # Note - dict(updates) work because our merge behavior is replace
    api = FakeSimpleUpdatesAPI([dict(updates)])
    # If we appy updates all at once, we expect just the final state
    delta = next(api.fetch_iter([], None))
    store.merge(collab, delta)
    store.flush()
    assert store.get_for_signal_type([collab], VideoMD5Signal) == {
        collab.name: expected_states[-1]
    }

    store = FakeFetchStore(FakeSimpleUpdatesAPI)  # type: ignore[arg-type]
    # If we appy updates 1-by-1 we expect all the end states
    api = FakeSimpleUpdatesAPI([dict([t]) for t in updates])
    for i, delta in enumerate(api.fetch_iter([], None)):
        store.merge(collab, delta)
        store.flush()
        assert store.get_for_signal_type([collab], VideoMD5Signal) == {
            collab.name: expected_states[i]
        }, f"Update {i}"
        assert store.get_checkpoint(collab) == delta.checkpoint
