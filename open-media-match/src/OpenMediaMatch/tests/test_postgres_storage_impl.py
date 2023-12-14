# Copyright (c) Meta Platforms, Inc. and affiliates.

from dataclasses import dataclass, field
import typing as t

import pytest
from flask import Flask

from OpenMediaMatch.tests.utils import app
from OpenMediaMatch.persistence import get_storage
from OpenMediaMatch.background_tasks import fetcher, build_index

from threatexchange.exchanges import fetch_state
from threatexchange.exchanges.impl.static_sample import StaticSampleSignalExchangeAPI
from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal

from OpenMediaMatch.storage.postgres.impl import DefaultOMMStore


@pytest.fixture()
def storage(app: Flask) -> t.Iterator[DefaultOMMStore]:
    storage_instance = get_storage()
    # We need these things to be true for the tests to pass
    assert isinstance(storage_instance, DefaultOMMStore)
    assert set(storage_instance.get_enabled_signal_types()) == {
        PdqSignal.get_name(),
        VideoMD5Signal.get_name(),
    }
    assert (
        StaticSampleSignalExchangeAPI.get_name()
        in storage_instance.exchange_get_type_configs()
    )
    yield storage_instance


def make_collab(storage: DefaultOMMStore) -> CollaborationConfigBase:
    cfg = CollaborationConfigBase(
        name="SAMPLE", api=StaticSampleSignalExchangeAPI.get_name(), enabled=True
    )
    storage.exchange_update(cfg, create=True)
    return cfg


def fetch(storage: DefaultOMMStore) -> None:
    fetcher.fetch_all(storage, storage.get_signal_type_configs())


def build(storage: DefaultOMMStore) -> None:
    build_index.build_all_indices(storage, storage, storage)


def fetch_build(storage: DefaultOMMStore) -> None:
    fetch(storage)
    build(storage)


def test_fetch_to_match_e2e(storage: DefaultOMMStore) -> None:
    cfg = make_collab(storage)
    fetch_build(storage)
    fetch_status = storage.exchange_get_fetch_status(cfg.name)
    expected_deltas = list(
        StaticSampleSignalExchangeAPI().fetch_iter(
            list(storage.get_enabled_signal_types().values()), None
        )
    )
    expected_fetch_count = sum(len(d.updates) for d in expected_deltas)
    assert fetch_status.up_to_date
    assert fetch_status.fetched_items == expected_fetch_count
    md5_index_status = storage.get_last_index_build_checkpoint(VideoMD5Signal)
    assert md5_index_status is not None
    assert md5_index_status.total_hash_count == len(VideoMD5Signal.get_examples())
    pdq_index_status = storage.get_last_index_build_checkpoint(PdqSignal)
    assert pdq_index_status is not None
    assert pdq_index_status.total_hash_count == len(PdqSignal.get_examples())
    md5_index = storage.get_signal_type_index(VideoMD5Signal)
    assert md5_index is not None
    vmd5_query_result = md5_index.query(VideoMD5Signal.get_examples()[0])
    assert len(vmd5_query_result) == 1
    empty_vmd5_query_result = md5_index.query(f"{8:032x}")
    assert not empty_vmd5_query_result

    # Someday, we could put some feedback here


@dataclass
class _FakeUpdateMaker:
    id: int = -1
    ids: set[int] = field(default_factory=set)

    def get_key(self, id: int) -> t.Tuple[str, str]:
        return (VideoMD5Signal.get_name(), f"{id:032x}")

    def get_next(self) -> t.Tuple[str, str]:
        self.id += 1
        self.ids.add(self.id)
        return self.get_key(self.id)

    def delete(self, id: int) -> t.Tuple[str, str]:
        self.ids.remove(id)
        return self.get_key(id)

    def get_multi(
        self, count: int
    ) -> t.Dict[t.Tuple[str, str], fetch_state.FetchedSignalMetadata | None]:
        return {
            self.get_next(): fetch_state.FetchedSignalMetadata() for i in range(count)
        }

    @property
    def count(self) -> int:
        return len(self.ids)

    @property
    def signals(self) -> set[str]:
        return {self.get_key(i)[1] for i in self.ids}


def test_sequential_fetch_updates(storage: DefaultOMMStore) -> None:
    cfg = make_collab(storage)
    checkpoint = StaticSampleSignalExchangeAPI.get_checkpoint_cls()()

    maker = _FakeUpdateMaker()

    # Update with some no-op deletes and an add
    update_1 = maker.get_multi(10)
    update_1.update(
        {
            ("", ""): None,
            maker.get_key(10001): None,
            maker.get_key(10002): None,
        }
    )

    def assert_content():
        target = storage.get_current_index_build_target(VideoMD5Signal)
        assert target is not None
        assert target.total_hash_count == maker.count
        signals = {s.signal_val for s in storage.bank_yield_content(VideoMD5Signal)}
        assert signals == maker.signals

    storage.exchange_commit_fetch(cfg, None, update_1, checkpoint)
    assert_content()

    meta = fetch_state.FetchedSignalMetadata

    # Update 2 - deletes and updates
    update_2 = {
        # delete 3 ids
        maker.delete(0): None,
        maker.delete(3): None,
        maker.delete(7): None,
        # Update 2 ids
        maker.get_key(1): meta(),
        maker.get_key(9): meta(),
    }
    update_2.update(maker.get_multi(2))
    storage.exchange_commit_fetch(cfg, checkpoint, update_2, checkpoint)
    assert_content()

    build(storage)
    md5_index_status = storage.get_last_index_build_checkpoint(VideoMD5Signal)
    assert md5_index_status is not None
    assert md5_index_status.total_hash_count == maker.count
