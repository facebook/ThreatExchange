# Copyright (c) Meta Platforms, Inc. and affiliates.

from dataclasses import dataclass, field
import typing as t

import pytest
from flask import Flask
from sqlalchemy import event, select

from OpenMediaMatch.tests.utils import app
from OpenMediaMatch.persistence import get_storage
from OpenMediaMatch.background_tasks import fetcher, build_index

from threatexchange.exchanges import fetch_state
from threatexchange.exchanges import auth
from threatexchange.exchanges.signal_exchange_api import TSignalExchangeAPICls
from threatexchange.exchanges.impl.static_sample import StaticSampleSignalExchangeAPI
from threatexchange.exchanges.impl.fb_threatexchange_api import (
    FBThreatExchangeSignalExchangeAPI,
    FBThreatExchangeCredentials,
)
from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal

from threatexchange.storage.interfaces import BankConfig, SignalExchangeAPIConfig
from OpenMediaMatch.storage.interface import BankContentConfig
from OpenMediaMatch.storage.postgres import database, impl
from OpenMediaMatch.storage.postgres.impl import (
    DefaultOMMStore,
    _BulkDbOpExchangeDataHelper,
    _sync_bankable_content,
)


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
        in storage_instance.exchange_apis_get_installed()
    )
    yield storage_instance


def make_collab(
    storage: DefaultOMMStore,
    *,
    api: TSignalExchangeAPICls = t.cast(
        TSignalExchangeAPICls, StaticSampleSignalExchangeAPI
    ),
    retain_data_with_unknown_signal_types: bool = False,
) -> CollaborationConfigBase:
    cfg = CollaborationConfigBase(name="SAMPLE", api=api.get_name(), enabled=True)
    storage.exchange_update(cfg, create=True)
    if retain_data_with_unknown_signal_types:
        sesh = database.db.session
        exchange = sesh.execute(
            select(database.ExchangeConfig).where(
                database.ExchangeConfig.name == cfg.name
            )
        ).scalar_one()
        exchange.retain_data_with_unknown_signal_types = True
        sesh.add(exchange)
        sesh.commit()

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


def test_recover_from_index_unlink_partial_failure(storage: DefaultOMMStore):
    """
    SignalTypeIndex is stored in the postgres large object
    As part of swapping over to the new index, we need to unlink the old
    interface, but there is a race here because unlinking may not happen
    in a transaction. See github.com/facebook/ThreatExchange/issues/1673
    """
    bank_cfg = BankConfig("TEST", matching_enabled_ratio=1.0)
    storage.bank_update(bank_cfg, create=True)
    storage.bank_add_content(
        bank_cfg.name, {VideoMD5Signal: VideoMD5Signal.get_examples()[0]}
    )

    def build_and_assert_ok():
        build(storage)
        index_status = storage.get_last_index_build_checkpoint(VideoMD5Signal)
        assert index_status.total_hash_count == 1
        index = storage.get_signal_type_index(VideoMD5Signal)
        assert index is not None

    build_and_assert_ok()

    # Now we'll fake that the large object borked
    index_record = database.db.session.execute(
        select(database.SignalIndex).where(
            database.SignalIndex.signal_type == VideoMD5Signal.get_name()
        )
    ).scalar_one()
    assert index_record.index_lobj_exists() is True
    raw_conn = database.db.engine.raw_connection()
    old_obj = raw_conn.lobject(index_record.serialized_index_large_object_oid, "n")
    old_obj.unlink()
    raw_conn.commit()

    # Now we should have a dangling record
    index_status = storage.get_last_index_build_checkpoint(VideoMD5Signal)
    assert index_status is None
    index = storage.get_signal_type_index(VideoMD5Signal)
    assert index is None

    # We should be able to recover by rebuilding
    build_and_assert_ok()


def test_bank_remove_content_scoped_to_bank(storage: DefaultOMMStore):
    for name in ("BANK_A", "BANK_B"):
        storage.bank_update(BankConfig(name, matching_enabled_ratio=1.0), create=True)
    content_id = storage.bank_add_content(
        "BANK_A", {VideoMD5Signal: VideoMD5Signal.get_examples()[0]}
    )

    assert storage.bank_remove_content("BANK_B", content_id) == 0
    assert len(storage.bank_content_get([content_id])) == 1

    assert storage.bank_remove_content("BANK_A", content_id) == 1
    assert storage.bank_content_get([content_id]) == []


def test_exchange_sync_removals_keep_other_content(
    storage: DefaultOMMStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Removing exchange content only removes that content: not other items from
    the same exchange, and not content in other banks.
    """
    local_signal = f"{99999:032x}"
    storage.bank_update(BankConfig("LOCAL", matching_enabled_ratio=1.0), create=True)
    local_id = storage.bank_add_content("LOCAL", {VideoMD5Signal: local_signal})

    cfg = make_collab(storage)
    checkpoint = StaticSampleSignalExchangeAPI.get_checkpoint_cls()()
    maker = _FakeUpdateMaker()
    storage.exchange_commit_fetch(cfg, None, maker.get_multi(3), checkpoint)

    def assert_content():
        signals = {s.signal_val for s in storage.bank_yield_content(VideoMD5Signal)}
        assert signals == maker.signals | {local_signal}
        assert len(storage.bank_content_get([local_id])) == 1

    assert_content()

    # Upstream deletes an item
    removed = {maker.delete(0): None}
    storage.exchange_commit_fetch(cfg, checkpoint, removed, checkpoint)
    assert_content()

    # Upstream updates an item to something we can no longer convert to signals
    monkeypatch.setattr(
        StaticSampleSignalExchangeAPI,
        "naive_convert_to_signal_type",
        classmethod(lambda cls, *args, **kwargs: {}),
    )
    unconvertible = {maker.delete(1): fetch_state.FetchedSignalMetadata()}
    storage.exchange_commit_fetch(cfg, checkpoint, unconvertible, checkpoint)
    monkeypatch.undo()
    assert_content()


def test_sync_bankable_content_deletes_only_listed_content(
    storage: DefaultOMMStore,
) -> None:
    """
    Regression: this delete used to run without a WHERE clause, removing every
    BankContent row in every bank.
    """
    storage.bank_update(BankConfig("LOCAL", matching_enabled_ratio=1.0), create=True)
    local_id = storage.bank_add_content(
        "LOCAL", {VideoMD5Signal: VideoMD5Signal.get_examples()[0]}
    )
    cfg = make_collab(storage)
    fetch(storage)

    sesh = database.db.session
    imported = (
        sesh.execute(
            select(database.BankContent).where(
                database.BankContent.imported_from_id.is_not(None)
            )
        )
        .scalars()
        .all()
    )
    assert len(imported) > 1
    target, *others = imported
    assert target.imported_from_id is not None

    op = _BulkDbOpExchangeDataHelper(
        exchange_data_id=target.imported_from_id,
        bank_content_id=target.id,
        existing_signals=[],
        update_as_signals={},
    )
    _sync_bankable_content({target.imported_from_id: op}, target.bank_id)
    sesh.commit()

    remaining = {
        bc.id
        for bc in storage.bank_content_get(
            [local_id, target.id] + [o.id for o in others]
        )
    }
    assert remaining == {local_id} | {o.id for o in others}


def test_sync_content_signal_bulk_deletes_only_stale_signals(
    app: Flask, storage: DefaultOMMStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    storage.bank_update(BankConfig("LOCAL", matching_enabled_ratio=1.0), create=True)
    md5_vals = [f"{i:032x}" for i in range(5)]
    pdq_val = PdqSignal.get_examples()[0]
    removed_id, changed_id, kept_id, untouched_id = (
        storage.bank_add_content("LOCAL", {VideoMD5Signal: v}) for v in md5_vals[:4]
    )
    multi_type_id = storage.bank_add_content(
        "LOCAL", {VideoMD5Signal: md5_vals[4], PdqSignal: pdq_val}
    )

    sesh = database.db.session
    contents = {
        bc.id: bc for bc in sesh.execute(select(database.BankContent)).scalars().all()
    }
    meta = fetch_state.FetchedSignalMetadata()
    changed_val = f"{100:032x}"
    updates: dict[int, dict[type[SignalType], dict[str, t.Any]]] = {
        removed_id: {},
        changed_id: {VideoMD5Signal: {changed_val: meta}},
        kept_id: {VideoMD5Signal: {md5_vals[2]: meta}},
        multi_type_id: {PdqSignal: {pdq_val: meta}},
    }
    ops = {
        content_id: _BulkDbOpExchangeDataHelper(
            exchange_data_id=None,
            bank_content_id=content_id,
            existing_signals=list(contents[content_id].signals),
            update_as_signals=update,
        )
        for content_id, update in updates.items()
    }

    delete_statements: list[str] = []

    def record_deletes(conn, cursor, statement, *args) -> None:
        if statement.lstrip().upper().startswith("DELETE FROM CONTENT_SIGNAL"):
            delete_statements.append(statement)

    monkeypatch.setitem(app.config, "CONTENT_SIGNAL_DELETE_CHUNK_SIZE", 2)
    event.listen(database.db.engine, "before_cursor_execute", record_deletes)
    try:
        impl._sync_content_signal(ops)
        sesh.commit()
    finally:
        event.remove(database.db.engine, "before_cursor_execute", record_deletes)

    # 3 stale signals (removed, changed, multi_type's md5) in chunks of 2
    assert len(delete_statements) == 2
    assert storage.bank_content_get_signals(
        [removed_id, changed_id, kept_id, untouched_id, multi_type_id]
    ) == {
        removed_id: {},
        changed_id: {VideoMD5Signal.get_name(): changed_val},
        kept_id: {VideoMD5Signal.get_name(): md5_vals[2]},
        untouched_id: {VideoMD5Signal.get_name(): md5_vals[3]},
        multi_type_id: {PdqSignal.get_name(): pdq_val},
    }


@pytest.mark.parametrize(
    "configured, expected",
    [
        (None, impl.DEFAULT_CONTENT_SIGNAL_DELETE_CHUNK_SIZE),
        (1, 1),
        ("250", 250),
        (impl.MAX_CONTENT_SIGNAL_DELETE_CHUNK_SIZE,) * 2,
    ],
)
def test_content_signal_delete_chunk_size(configured: t.Any, expected: int) -> None:
    config = (
        {} if configured is None else {"CONTENT_SIGNAL_DELETE_CHUNK_SIZE": configured}
    )
    assert impl._content_signal_delete_chunk_size(config) == expected


@pytest.mark.parametrize(
    "configured",
    [0, -1, impl.MAX_CONTENT_SIGNAL_DELETE_CHUNK_SIZE + 1, "abc", "1.5", 1.5, True],
)
def test_content_signal_delete_chunk_size_rejects_invalid(configured: t.Any) -> None:
    with pytest.raises(ValueError, match="CONTENT_SIGNAL_DELETE_CHUNK_SIZE"):
        impl._content_signal_delete_chunk_size(
            {"CONTENT_SIGNAL_DELETE_CHUNK_SIZE": configured}
        )


def test_exchange_fetch_removes_signal_types_dropped_upstream(
    storage: DefaultOMMStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg = make_collab(storage)
    checkpoint = StaticSampleSignalExchangeAPI.get_checkpoint_cls()()
    md5_val = f"{1:032x}"
    pdq_val = PdqSignal.get_examples()[0]
    meta = fetch_state.FetchedSignalMetadata()
    converted: dict[type[SignalType], dict[str, t.Any]] = {
        VideoMD5Signal: {md5_val: meta},
        PdqSignal: {pdq_val: meta},
    }
    monkeypatch.setattr(
        StaticSampleSignalExchangeAPI,
        "naive_convert_to_signal_type",
        classmethod(lambda cls, *args, **kwargs: converted),
    )
    key = (VideoMD5Signal.get_name(), md5_val)
    storage.exchange_commit_fetch(cfg, None, {key: meta}, checkpoint)

    def signals() -> set[tuple[str, str]]:
        return {
            (s.signal_type_name, s.signal_val) for s in storage.bank_yield_content()
        }

    assert signals() == {
        (VideoMD5Signal.get_name(), md5_val),
        (PdqSignal.get_name(), pdq_val),
    }

    del converted[VideoMD5Signal]
    storage.exchange_commit_fetch(cfg, checkpoint, {key: meta}, checkpoint)
    assert signals() == {(PdqSignal.get_name(), pdq_val)}


class _UnknownSampleExchangeAPI(StaticSampleSignalExchangeAPI):
    """Returns all the sample data, but can't convert to any types"""

    @classmethod
    def get_name(cls) -> str:
        return "sample_unknown"

    @classmethod
    def naive_convert_to_signal_type(
        cls,
        signal_types: t.Sequence[t.Type[SignalType]],
        collab: CollaborationConfigBase,
        fetched: t.Mapping[
            t.Tuple[str, str], t.Optional[fetch_state.TFetchedSignalMetadata]
        ],
    ) -> t.Dict[t.Type[SignalType], t.Dict[str, fetch_state.TFetchedSignalMetadata]]:
        return {}


def test_exchange_type_confg(storage: DefaultOMMStore):
    # Configs should always exist for all configured types
    existing = storage.exchange_apis_get_configs()
    assert set(existing) == set(storage.exchange_apis_get_installed())

    fb_auth = FBThreatExchangeCredentials(f"{0:08}|{0:020}")

    # Can't set a config type that doesn't exist
    with pytest.raises(Exception):
        storage.exchange_api_config_update(
            SignalExchangeAPIConfig(
                t.cast(TSignalExchangeAPICls, _UnknownSampleExchangeAPI),
                fb_auth,
            ),
        )

    new_exchange_types = dict(storage.exchange_types)
    api_name = FBThreatExchangeSignalExchangeAPI.get_name()
    new_exchange_types[api_name] = t.cast(
        TSignalExchangeAPICls, FBThreatExchangeSignalExchangeAPI
    )
    storage.exchange_types = new_exchange_types

    # Sanity, no db record yet
    api_config = storage.exchange_apis_get_configs().get(api_name)
    assert api_config is not None
    assert api_config.api_cls is FBThreatExchangeSignalExchangeAPI
    assert api_config.credentials is None

    # Can't set credentials for something that doesn't take it
    with pytest.raises(Exception):
        storage.exchange_api_config_update(
            SignalExchangeAPIConfig(
                t.cast(TSignalExchangeAPICls, StaticSampleSignalExchangeAPI),
                auth.CredentialHelper(),
            ),
        )

    val_to_set = SignalExchangeAPIConfig(
        t.cast(TSignalExchangeAPICls, FBThreatExchangeSignalExchangeAPI),
        fb_auth,
    )
    storage.exchange_api_config_update(val_to_set)
    assert val_to_set == storage.exchange_apis_get_configs().get(api_name)


def test_exchange_get_data(storage: DefaultOMMStore):
    cfg = make_collab(storage)
    fetch(storage)
    patched_signal_types = dict(storage.exchange_types)
    patched_signal_types[_UnknownSampleExchangeAPI.get_name()] = t.cast(
        TSignalExchangeAPICls, _UnknownSampleExchangeAPI
    )
    storage.exchange_types = patched_signal_types

    signal_types = list(storage.get_enabled_signal_types().values())

    # Storing original data not exposed by default
    for delta in StaticSampleSignalExchangeAPI().fetch_iter(signal_types, None):
        example_key, example_metadata = next(iter(delta.updates.items()))
        break

    with pytest.raises(KeyError):
        storage.exchange_get_data("No such collab", example_key)

    with pytest.raises(KeyError):
        storage.exchange_get_data(cfg.name, "no such key")

    val = storage.exchange_get_data(cfg.name, example_key)
    assert val == example_metadata

    storage.exchange_delete(cfg.name)
    # pretend like we don't know what any signal types are
    cfg = make_collab(
        storage, api=t.cast(TSignalExchangeAPICls, _UnknownSampleExchangeAPI)
    )
    fetch(storage)

    # We don't store the unknown signal type
    with pytest.raises(KeyError):
        storage.exchange_get_data(cfg.name, example_key)

    # Unless we specifically configure to do so
    storage.exchange_delete(cfg.name)
    cfg = make_collab(storage, retain_data_with_unknown_signal_types=True)
    fetch(storage)

    val = storage.exchange_get_data(cfg.name, example_key)
    assert val == example_metadata


def test_bank_content_note(storage: DefaultOMMStore) -> None:
    """Test adding, reading, and updating notes on bank content."""
    bank_cfg = BankConfig("TEST_NOTES", matching_enabled_ratio=1.0)
    storage.bank_update(bank_cfg, create=True)

    # Test adding content without a note
    content_id_no_note = storage.bank_add_content(
        bank_cfg.name, {VideoMD5Signal: VideoMD5Signal.get_examples()[0]}
    )
    content_configs = storage.bank_content_get([content_id_no_note])
    assert len(content_configs) == 1
    assert content_configs[0].note is None

    # Test adding content with a note
    note_text = "Reported by user123 on 2024-01-15"
    content_config_with_note = BankContentConfig(
        id=0,
        disable_until_ts=BankContentConfig.ENABLED,
        collab_metadata={},
        original_media_uri="http://example.com/image.jpg",
        bank=bank_cfg,
        note=note_text,
    )
    content_id_with_note = storage.bank_add_content(
        bank_cfg.name,
        {VideoMD5Signal: f"{1:032x}"},
        config=content_config_with_note,
    )
    content_configs = storage.bank_content_get([content_id_with_note])
    assert len(content_configs) == 1
    assert content_configs[0].note == note_text

    # Test updating a note
    updated_note = "Updated: confirmed malicious"
    content_configs[0].note = updated_note
    storage.bank_content_update(content_configs[0])

    # Verify the update persisted
    content_configs = storage.bank_content_get([content_id_with_note])
    assert content_configs[0].note == updated_note

    # Test clearing a note (setting to None)
    content_configs[0].note = None
    storage.bank_content_update(content_configs[0])

    content_configs = storage.bank_content_get([content_id_with_note])
    assert content_configs[0].note is None


def test_bank_content_note_max_length(storage: DefaultOMMStore) -> None:
    """Test that notes respect the 255 character limit."""
    bank_cfg = BankConfig("TEST_NOTE_LENGTH", matching_enabled_ratio=1.0)
    storage.bank_update(bank_cfg, create=True)

    # Test with exactly 255 characters (should work)
    note_255 = "a" * 255
    content_config = BankContentConfig(
        id=0,
        disable_until_ts=BankContentConfig.ENABLED,
        collab_metadata={},
        original_media_uri=None,
        bank=bank_cfg,
        note=note_255,
    )
    content_id = storage.bank_add_content(
        bank_cfg.name,
        {VideoMD5Signal: f"{2:032x}"},
        config=content_config,
    )
    content_configs = storage.bank_content_get([content_id])
    assert content_configs[0].note is not None
    assert len(content_configs[0].note) == 255

    # Test with 256 characters (should fail)
    note_256 = "a" * 256
    content_config_over = BankContentConfig(
        id=0,
        disable_until_ts=BankContentConfig.ENABLED,
        collab_metadata={},
        original_media_uri=None,
        bank=bank_cfg,
        note=note_256,
    )
    with pytest.raises(Exception):
        storage.bank_add_content(
            bank_cfg.name,
            {VideoMD5Signal: f"{3:032x}"},
            config=content_config_over,
        )
