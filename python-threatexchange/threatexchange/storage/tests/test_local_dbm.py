# Copyright (c) Meta Platforms, Inc. and affiliates.

import dbm
import importlib
from dataclasses import dataclass, field
import pathlib
import time
import typing as t
from unittest.mock import patch

import pytest

from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.exchanges.fetch_state import (
    FetchedSignalMetadata,
    NoCheckpointing,
)
from threatexchange.exchanges.impl.static_sample import StaticSampleSignalExchangeAPI
from threatexchange.exchanges.impl.fb_threatexchange_api import (
    FBThreatExchangeCollabConfig,
    FBThreatExchangeSignalExchangeAPI,
)
from threatexchange.storage import interfaces as iface
from threatexchange.storage import local_dbm
from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.signal_base import SignalType


def test_signal_type(tmpdir: pathlib.Path):
    storage: iface.ISignalTypeConfigStore = local_dbm.DBMStore(pathlib.Path(tmpdir))

    # Get with unset values
    cfgs = storage.get_signal_type_configs()
    assert set(cfgs) == {"pdq", "video_md5"}
    for val in cfgs.values():
        assert val.enabled_ratio == 1.0

    # Override one
    storage.create_or_update_signal_type_override("pdq", 0.5)
    cfgs = storage.get_signal_type_configs()
    assert set(cfgs) == {"pdq", "video_md5"}
    assert cfgs["pdq"].enabled_ratio == 0.5
    assert cfgs["video_md5"].enabled_ratio == 1.0


def test_content_type(tmpdir: pathlib.Path):
    storage = local_dbm.DBMStore(pathlib.Path(tmpdir))

    # Get with unset values — all enabled by default
    cfgs = storage.get_content_type_configs()
    assert set(cfgs) == {"photo", "video"}
    for val in cfgs.values():
        assert val.enabled is True

    # Override one
    storage._create_or_update_content_type_override("photo", False)
    cfgs = storage.get_content_type_configs()
    assert set(cfgs) == {"photo", "video"}
    assert cfgs["photo"].enabled is False
    assert cfgs["video"].enabled is True


def _make_store(tmpdir: pathlib.Path) -> local_dbm.DBMStore:
    return local_dbm.DBMStore(
        pathlib.Path(tmpdir),
        exchange_types=[
            StaticSampleSignalExchangeAPI,  # type: ignore[list-item]
            FBThreatExchangeSignalExchangeAPI,  # type: ignore[list-item]
        ],
    )


def _make_collab(name: str = "test_collab") -> CollaborationConfigBase:
    return CollaborationConfigBase(
        name=name, api=StaticSampleSignalExchangeAPI.get_name(), enabled=True
    )


def _make_tx_collab(
    name: str = "tx_collab", privacy_group: int = 12345, enabled: bool = True
) -> FBThreatExchangeCollabConfig:
    return FBThreatExchangeCollabConfig(
        name=name, enabled=enabled, privacy_group=privacy_group
    )


def test_exchange_apis_get_configs(tmpdir: pathlib.Path) -> None:
    store = _make_store(tmpdir)

    cfgs = store.exchange_apis_get_configs()
    assert set(cfgs) == {"sample", FBThreatExchangeSignalExchangeAPI.get_name()}

    sample_cfg = cfgs["sample"]
    assert sample_cfg.api_cls is StaticSampleSignalExchangeAPI
    assert sample_cfg.credentials is None
    assert sample_cfg.supports_auth is False

    tx_cfg = cfgs[FBThreatExchangeSignalExchangeAPI.get_name()]
    assert tx_cfg.api_cls is FBThreatExchangeSignalExchangeAPI
    assert tx_cfg.credentials is None
    assert tx_cfg.supports_auth is True


def test_exchange_api_config_update(tmpdir: pathlib.Path) -> None:
    store = _make_store(tmpdir)

    # StaticSampleSignalExchangeAPI doesn't support auth; update with no credentials
    cfg = iface.SignalExchangeAPIConfig(
        api_cls=StaticSampleSignalExchangeAPI  # type: ignore[arg-type]
    )
    store.exchange_api_config_update(cfg)

    cfgs = store.exchange_apis_get_configs()
    assert cfgs["sample"].credentials is None


def test_exchange_crud(tmpdir: pathlib.Path) -> None:
    store = _make_store(tmpdir)
    collab = _make_collab()

    # Initially empty
    assert store.exchanges_get() == {}

    # Create
    store.exchange_update(collab, create=True)
    collabs = store.exchanges_get()
    assert set(collabs) == {"test_collab"}
    assert collabs["test_collab"].name == "test_collab"
    assert collabs["test_collab"].api == "sample"
    assert collabs["test_collab"].enabled is True

    # Duplicate create raises
    with pytest.raises(ValueError, match="already exists"):
        store.exchange_update(collab, create=True)

    # Update (no create flag)
    updated = CollaborationConfigBase(
        name="test_collab", api=StaticSampleSignalExchangeAPI.get_name(), enabled=False
    )
    store.exchange_update(updated)
    assert store.exchanges_get()["test_collab"].enabled is False

    # Update non-existent raises
    with pytest.raises(ValueError, match="does not exist"):
        store.exchange_update(_make_collab("nonexistent"))

    # Delete
    store.exchange_delete("test_collab")
    assert store.exchanges_get() == {}

    # Delete non-existent is a no-op
    store.exchange_delete("test_collab")


def test_exchange_crud_tx_collab(tmpdir: pathlib.Path) -> None:
    """Test CRUD using FBThreatExchangeCollabConfig, which has a custom privacy_group field."""
    store = _make_store(tmpdir)

    # Create with initial privacy group
    collab = _make_tx_collab(privacy_group=11111)
    store.exchange_update(collab, create=True)

    collabs = store.exchanges_get()
    assert set(collabs) == {"tx_collab"}
    stored = collabs["tx_collab"]
    assert isinstance(stored, FBThreatExchangeCollabConfig)
    assert stored.privacy_group == 11111
    assert stored.enabled is True

    # Update: change both privacy_group and enabled
    updated = _make_tx_collab(privacy_group=99999, enabled=False)
    store.exchange_update(updated)

    collabs = store.exchanges_get()
    stored = collabs["tx_collab"]
    assert isinstance(stored, FBThreatExchangeCollabConfig)
    assert stored.privacy_group == 99999
    assert stored.enabled is False

    # Delete
    store.exchange_delete("tx_collab")
    assert store.exchanges_get() == {}


def test_exchange_fetch_lifecycle(tmpdir: pathlib.Path) -> None:
    store = _make_store(tmpdir)
    collab = _make_collab()
    store.exchange_update(collab, create=True)

    # Initial status
    status = store.exchange_get_fetch_status("test_collab")
    assert status.fetch_in_progress is False
    assert status.last_fetch_complete_ts is None
    assert status.fetched_items == 0

    # Start fetch
    store.exchange_start_fetch("test_collab")
    status = store.exchange_get_fetch_status("test_collab")
    assert status.fetch_in_progress is True

    # Complete fetch (success)
    store.exchange_complete_fetch("test_collab", is_up_to_date=True, exception=False)
    status = store.exchange_get_fetch_status("test_collab")
    assert status.fetch_in_progress is False
    assert status.last_fetch_complete_ts is not None
    assert status.last_fetch_succeeded is True
    assert status.up_to_date is True

    # Complete fetch (exception)
    store.exchange_complete_fetch("test_collab", is_up_to_date=False, exception=True)
    status = store.exchange_get_fetch_status("test_collab")
    assert status.last_fetch_succeeded is False
    assert status.up_to_date is False


def test_exchange_commit_and_checkpoint(tmpdir: pathlib.Path) -> None:
    store = _make_store(tmpdir)
    collab = _make_collab()
    store.exchange_update(collab, create=True)

    # No checkpoint before any fetch
    assert store.exchange_get_fetch_checkpoint("test_collab") is None

    from threatexchange.exchanges.fetch_state import FetchedSignalMetadata

    checkpoint = NoCheckpointing()
    dat: dict = {
        (
            "pdq",
            "abc123",
        ): None,  # will be ignored (None = delete, but nothing to delete)
        ("pdq", "def456"): FetchedSignalMetadata(),
        ("video_md5", "hash789"): FetchedSignalMetadata(),
    }

    store.exchange_commit_fetch(collab, None, dat, checkpoint)

    # Checkpoint roundtrip
    stored_cp = store.exchange_get_fetch_checkpoint("test_collab")
    assert isinstance(stored_cp, NoCheckpointing)

    # Item count: 2 non-None values stored
    status = store.exchange_get_fetch_status("test_collab")
    assert status.fetched_items == 2

    # Delete one item via None value
    store.exchange_commit_fetch(
        collab, checkpoint, {("pdq", "def456"): None}, NoCheckpointing()
    )
    status = store.exchange_get_fetch_status("test_collab")
    assert status.fetched_items == 1


def test_exchange_get_client(tmpdir: pathlib.Path) -> None:
    store = _make_store(tmpdir)
    collab = _make_collab()
    store.exchange_update(collab, create=True)

    client = store.exchange_get_client(collab)
    assert isinstance(client, StaticSampleSignalExchangeAPI)


def test_exchange_get_data(tmpdir: pathlib.Path) -> None:
    """exchange_get_data returns the stored FetchedSignalMetadata for a key."""
    from threatexchange.exchanges.fetch_state import FetchedSignalMetadata

    store = _make_store(tmpdir)
    collab = _make_collab()
    store.exchange_update(collab, create=True)

    # Spoof fetch data using StaticSampleSignalExchangeAPI's record type
    dat: dict = {
        ("pdq", "abc123"): FetchedSignalMetadata(),
        ("pdq", "def456"): FetchedSignalMetadata(),
        ("video_md5", "hash789"): FetchedSignalMetadata(),
    }
    store.exchange_commit_fetch(collab, None, dat, NoCheckpointing())

    # Retrieve each stored record
    result = store.exchange_get_data("test_collab", ("pdq", "abc123"))
    assert isinstance(result, FetchedSignalMetadata)

    result2 = store.exchange_get_data("test_collab", ("video_md5", "hash789"))
    assert isinstance(result2, FetchedSignalMetadata)

    # Missing key raises KeyError
    with pytest.raises(KeyError):
        store.exchange_get_data("test_collab", ("pdq", "not_stored"))

    # Missing collab raises KeyError
    with pytest.raises(KeyError):
        store.exchange_get_data("no_such_collab", ("pdq", "abc123"))

    # After deletion, data is gone
    store.exchange_delete("test_collab")
    with pytest.raises(KeyError):
        store.exchange_get_data("test_collab", ("pdq", "abc123"))


# IBankStore tests


def _make_bank(name: str = "TEST_BANK", ratio: float = 1.0) -> iface.BankConfig:
    return iface.BankConfig(name=name, matching_enabled_ratio=ratio)


def test_bank_create_get_delete(tmpdir: pathlib.Path) -> None:
    store = local_dbm.DBMStore(pathlib.Path(tmpdir))

    # Initially empty
    assert store.get_banks() == {}

    # Create
    bank = _make_bank()
    store.bank_update(bank, create=True)
    banks = store.get_banks()
    assert set(banks) == {"TEST_BANK"}
    assert banks["TEST_BANK"].name == "TEST_BANK"
    assert banks["TEST_BANK"].matching_enabled_ratio == 1.0

    # get_bank helper
    assert store.get_bank("TEST_BANK") is not None
    assert store.get_bank("NO_SUCH") is None

    # Duplicate create raises
    with pytest.raises(ValueError, match="already exists"):
        store.bank_update(bank, create=True)

    # Update (no create flag)
    updated = _make_bank(ratio=0.5)
    store.bank_update(updated)
    fetched = store.get_bank("TEST_BANK")
    assert fetched is not None
    assert fetched.matching_enabled_ratio == 0.5

    # Update non-existent raises
    with pytest.raises(ValueError, match="does not exist"):
        store.bank_update(_make_bank("GHOST"))

    # Delete
    store.bank_delete("TEST_BANK")
    assert store.get_banks() == {}

    # Delete non-existent is a no-op
    store.bank_delete("TEST_BANK")


def test_bank_add_content_and_retrieve(tmpdir: pathlib.Path) -> None:
    store = local_dbm.DBMStore(pathlib.Path(tmpdir))
    store.bank_update(_make_bank(), create=True)

    # Add content with one signal type
    pdq_val = "a" * 64
    cid = store.bank_add_content("TEST_BANK", {PdqSignal: pdq_val})
    assert isinstance(cid, int)
    assert cid >= 1

    # Retrieve it
    results = store.bank_content_get([cid])
    assert len(results) == 1
    result = results[0]
    assert result.id == cid
    assert result.bank.name == "TEST_BANK"
    assert result.disable_until_ts == iface.BankContentConfig.ENABLED

    # Requesting a non-existent ID returns nothing
    assert store.bank_content_get([99999]) == []


def test_bank_content_signals(tmpdir: pathlib.Path) -> None:
    store = local_dbm.DBMStore(pathlib.Path(tmpdir))
    store.bank_update(_make_bank(), create=True)

    pdq_val = "b" * 64
    md5_val = "c" * 32
    cid = store.bank_add_content(
        "TEST_BANK", {PdqSignal: pdq_val, VideoMD5Signal: md5_val}
    )

    signals = store.bank_content_get_signals([cid])
    assert cid in signals
    assert signals[cid][PdqSignal.get_name()] == pdq_val
    assert signals[cid][VideoMD5Signal.get_name()] == md5_val

    # Non-existent ID returns empty mapping
    assert store.bank_content_get_signals([99999]) == {}


def test_bank_unique_ids(tmpdir: pathlib.Path) -> None:
    store = local_dbm.DBMStore(pathlib.Path(tmpdir))
    store.bank_update(_make_bank("BANK_A"), create=True)
    store.bank_update(_make_bank("BANK_B"), create=True)

    pdq_val = "d" * 64
    ids = [
        store.bank_add_content("BANK_A", {PdqSignal: pdq_val}),
        store.bank_add_content("BANK_B", {PdqSignal: pdq_val}),
        store.bank_add_content("BANK_A", {PdqSignal: pdq_val}),
    ]
    assert len(set(ids)) == 3, "all IDs must be globally unique"

    # bank_content_get can retrieve across banks
    results = store.bank_content_get(ids)
    assert len(results) == 3
    bank_names = {r.bank.name for r in results}
    assert bank_names == {"BANK_A", "BANK_B"}


def test_bank_remove_content(tmpdir: pathlib.Path) -> None:
    store = local_dbm.DBMStore(pathlib.Path(tmpdir))
    store.bank_update(_make_bank(), create=True)

    cid = store.bank_add_content("TEST_BANK", {PdqSignal: "e" * 64})
    assert store.bank_content_get([cid]) != []

    removed = store.bank_remove_content("TEST_BANK", cid)
    assert removed == 1
    assert store.bank_content_get([cid]) == []

    # Removing again returns 0
    assert store.bank_remove_content("TEST_BANK", cid) == 0


def test_bank_content_update(tmpdir: pathlib.Path) -> None:
    store = local_dbm.DBMStore(pathlib.Path(tmpdir))
    store.bank_update(_make_bank(), create=True)

    cid = store.bank_add_content("TEST_BANK", {PdqSignal: "f" * 64})
    original = store.bank_content_get([cid])[0]
    assert original.disable_until_ts == iface.BankContentConfig.ENABLED

    # Disable it
    disabled = iface.BankContentConfig(
        id=cid,
        disable_until_ts=iface.BankContentConfig.DISABLED,
        collab_metadata={},
        original_media_uri=None,
        bank=original.bank,
    )
    store.bank_content_update(disabled)
    updated = store.bank_content_get([cid])[0]
    assert updated.disable_until_ts == iface.BankContentConfig.DISABLED

    # Signals are preserved after update
    signals = store.bank_content_get_signals([cid])
    assert signals[cid][PdqSignal.get_name()] == "f" * 64


def test_bank_yield_content(tmpdir: pathlib.Path) -> None:
    store = local_dbm.DBMStore(pathlib.Path(tmpdir))
    store.bank_update(_make_bank("BANK_A"), create=True)
    store.bank_update(_make_bank("BANK_B"), create=True)

    pdq_val = "1" * 64
    md5_val = "2" * 32
    store.bank_add_content("BANK_A", {PdqSignal: pdq_val, VideoMD5Signal: md5_val})
    store.bank_add_content("BANK_B", {PdqSignal: "3" * 64})

    # Yield all: 2 PDQ + 1 MD5 = 3 items
    all_items = list(store.bank_yield_content())
    assert len(all_items) == 3

    # Yield filtered to PDQ: 2 items
    pdq_items = list(store.bank_yield_content(signal_type=PdqSignal))
    assert len(pdq_items) == 2
    assert all(item.signal_type_name == PdqSignal.get_name() for item in pdq_items)

    # Yield filtered to MD5: 1 item
    md5_items = list(store.bank_yield_content(signal_type=VideoMD5Signal))
    assert len(md5_items) == 1
    assert md5_items[0].signal_val == md5_val


def test_index_build_target(tmpdir: pathlib.Path) -> None:
    store = local_dbm.DBMStore(pathlib.Path(tmpdir))

    # Empty store returns get_empty()
    target = store.get_current_index_build_target(PdqSignal)
    assert target.total_hash_count == 0
    assert target.last_item_id == -1

    store.bank_update(_make_bank(), create=True)
    store.bank_add_content("TEST_BANK", {PdqSignal: "a" * 64})
    store.bank_add_content("TEST_BANK", {PdqSignal: "b" * 64, VideoMD5Signal: "c" * 32})
    store.bank_add_content("TEST_BANK", {VideoMD5Signal: "d" * 32})

    pdq_target = store.get_current_index_build_target(PdqSignal)
    assert pdq_target.total_hash_count == 2

    md5_target = store.get_current_index_build_target(VideoMD5Signal)
    assert md5_target.total_hash_count == 2


def test_bank_add_content_unknown_bank(tmpdir: pathlib.Path) -> None:
    store = local_dbm.DBMStore(pathlib.Path(tmpdir))
    with pytest.raises(KeyError, match="NO_BANK"):
        store.bank_add_content("NO_BANK", {PdqSignal: "a" * 64})


def _dbm_files(folder: pathlib.Path, base: str) -> t.List[pathlib.Path]:
    """Files that some dbm backend created for `base` in folder."""
    return [
        folder / (base + ext)
        for ext in ("", ".db", ".dir", ".dat", ".bak")
        if (folder / (base + ext)).exists()
    ]


def test_delete_and_rename_find_files(tmpdir: pathlib.Path) -> None:
    folder = pathlib.Path(tmpdir)
    store = _make_store(folder)

    collab = _make_collab()
    store.exchange_update(collab, create=True)
    store.exchange_commit_fetch(
        collab, None, {("pdq", "a" * 64): FetchedSignalMetadata()}, NoCheckpointing()
    )
    assert _dbm_files(folder / "exchange_data", "test_collab")
    store.exchange_delete("test_collab")
    # Deleting clears the db rather than removing its files
    with dbm.open(str(folder / "exchange_data" / "test_collab")) as db:
        assert len(db) == 0

    store.bank_update(_make_bank("OLD"), create=True)
    cid = store.bank_add_content("OLD", {PdqSignal: "a" * 64})
    store.bank_update(_make_bank("NEW"), rename_from="OLD")
    assert not _dbm_files(folder / "bank_content", "OLD")
    assert _dbm_files(folder / "bank_content", "NEW")
    assert [c.id for c in store.bank_content_get([cid])] == [cid]

    store.bank_delete("NEW")
    with dbm.open(str(folder / "bank_content" / "NEW")) as db:
        assert len(db) == 0


def test_state_version(tmpdir: pathlib.Path) -> None:
    folder = pathlib.Path(tmpdir)
    version_file = folder / local_dbm.STATE_VERSION_FILENAME

    assert local_dbm.DBMStore.read_state_version(folder) is None
    local_dbm.DBMStore(folder)
    # Not written yet - see legacy CLI state migration (#1754)
    assert not version_file.exists()

    version_file.write_text(f"{local_dbm.STATE_VERSION}\n")
    assert local_dbm.DBMStore.read_state_version(folder) == local_dbm.STATE_VERSION
    local_dbm.DBMStore(folder)

    version_file.write_text(str(local_dbm.STATE_VERSION + 1))
    with pytest.raises(ValueError, match="newer version"):
        local_dbm.DBMStore(folder)

    version_file.write_text("garbage")
    with pytest.raises(ValueError, match="Unparsable"):
        local_dbm.DBMStore.read_state_version(folder)


def test_signal_type_index_store(tmpdir: pathlib.Path) -> None:
    folder = pathlib.Path(tmpdir)
    store: iface.ISignalTypeIndexStore = local_dbm.DBMStore(folder)
    # Note: indices have 2+ entries because a single-entry PDQ (faiss
    # IndexBinaryMultiHash) index doesn't survive serialization.

    # Nothing stored yet
    assert store.get_signal_type_index(PdqSignal) is None
    assert store.get_last_index_build_checkpoint(PdqSignal) is None

    pdq_a = "a" * 64
    pdq_b = "b" * 64
    pdq_c = "c" * 64
    checkpoint = iface.SignalTypeIndexBuildCheckpoint(
        last_item_timestamp=100, last_item_id=3, total_hash_count=2
    )
    store.store_signal_type_index(
        PdqSignal, PdqSignal.get_index_cls().build([(pdq_a, 1), (pdq_c, 3)]), checkpoint
    )
    assert (folder / local_dbm.INDEX_FOLDER_NAME / "pdq.index").is_file()

    index = store.get_signal_type_index(PdqSignal)
    assert index is not None
    assert [m.metadata for m in index.query(pdq_a)] == [1]
    assert store.get_last_index_build_checkpoint(PdqSignal) == checkpoint

    # Other signal types are unaffected
    assert store.get_signal_type_index(VideoMD5Signal) is None
    assert store.get_last_index_build_checkpoint(VideoMD5Signal) is None

    # Replace
    checkpoint2 = iface.SignalTypeIndexBuildCheckpoint(
        last_item_timestamp=200, last_item_id=3, total_hash_count=2
    )
    store.store_signal_type_index(
        PdqSignal,
        PdqSignal.get_index_cls().build([(pdq_b, 2), (pdq_c, 3)]),
        checkpoint2,
    )
    index = store.get_signal_type_index(PdqSignal)
    assert index is not None
    assert index.query(pdq_a) == []
    assert [m.metadata for m in index.query(pdq_b)] == [2]
    assert store.get_last_index_build_checkpoint(PdqSignal) == checkpoint2

    # Survives reopening the store
    reopened = local_dbm.DBMStore(folder)
    assert reopened.get_last_index_build_checkpoint(PdqSignal) == checkpoint2
    index = reopened.get_signal_type_index(PdqSignal)
    assert index is not None
    assert [m.metadata for m in index.query(pdq_b)] == [2]

    # A checkpoint without its index file isn't trusted
    (folder / local_dbm.INDEX_FOLDER_NAME / "pdq.index").unlink()
    assert store.get_signal_type_index(PdqSignal) is None
    assert store.get_last_index_build_checkpoint(PdqSignal) is None


def test_signal_type_index_store_failed_write(tmpdir: pathlib.Path) -> None:
    folder = pathlib.Path(tmpdir)
    store = local_dbm.DBMStore(folder)
    pdq_a = "a" * 64
    pdq_c = "c" * 64
    checkpoint = iface.SignalTypeIndexBuildCheckpoint(
        last_item_timestamp=100, last_item_id=3, total_hash_count=2
    )
    store.store_signal_type_index(
        PdqSignal, PdqSignal.get_index_cls().build([(pdq_a, 1), (pdq_c, 3)]), checkpoint
    )

    bad_index = PdqSignal.get_index_cls().build([("b" * 64, 2), (pdq_c, 3)])

    def explode(fout: t.BinaryIO) -> None:
        fout.write(b"partial")
        raise RuntimeError("disk full")

    bad_index.serialize = explode  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="disk full"):
        store.store_signal_type_index(
            PdqSignal,
            bad_index,
            iface.SignalTypeIndexBuildCheckpoint(
                last_item_timestamp=200, last_item_id=3, total_hash_count=2
            ),
        )

    # Previous index and checkpoint intact, no temp files left behind
    index = store.get_signal_type_index(PdqSignal)
    assert index is not None
    assert [m.metadata for m in index.query(pdq_a)] == [1]
    assert store.get_last_index_build_checkpoint(PdqSignal) == checkpoint
    assert [p.name for p in (folder / local_dbm.INDEX_FOLDER_NAME).iterdir()] == [
        "pdq.index"
    ]


# exchange_commit_fetch: merge + bank-per-collab


@dataclass
class _IdKeyedRecord(FetchedSignalMetadata):
    pdq: t.Optional[str] = None
    tags: t.List[str] = field(default_factory=list)
    deleted: bool = False


class _IdKeyedAPI(StaticSampleSignalExchangeAPI):
    """
    Records keyed by id rather than by signal, with a non-trivial merge.

    Merging unions the tags with the stored record, and a deleted record
    is removed, similar to NCMEC.
    """

    @classmethod
    def get_name(cls) -> str:
        return "id_keyed"

    @staticmethod
    def get_record_cls() -> t.Type[_IdKeyedRecord]:
        return _IdKeyedRecord

    @classmethod
    def fetch_value_merge(  # type: ignore[override]
        cls, old: t.Optional[_IdKeyedRecord], new: t.Optional[_IdKeyedRecord]
    ) -> t.Optional[_IdKeyedRecord]:
        assert new is not None
        if new.deleted:
            return None
        if old is not None:
            new.tags = sorted(set(old.tags) | set(new.tags))
        return new

    @classmethod
    def naive_convert_to_signal_type(  # type: ignore[override]
        cls,
        signal_types: t.Sequence[t.Type[SignalType]],
        collab: CollaborationConfigBase,
        fetched: t.Mapping[str, _IdKeyedRecord],
    ) -> t.Dict[t.Type[SignalType], t.Dict[str, _IdKeyedRecord]]:
        ret: t.Dict[t.Type[SignalType], t.Dict[str, _IdKeyedRecord]] = {}
        for record in fetched.values():
            if record.pdq is not None and PdqSignal in signal_types:
                ret.setdefault(PdqSignal, {})[record.pdq] = record
        return ret


PDQ_A = "a" * 64
PDQ_B = "b" * 64
MD5_A = "a" * 32


def _make_id_keyed_store(tmpdir: pathlib.Path) -> local_dbm.DBMStore:
    store = local_dbm.DBMStore(
        pathlib.Path(tmpdir),
        exchange_types=[
            StaticSampleSignalExchangeAPI,  # type: ignore[list-item]
            _IdKeyedAPI,  # type: ignore[list-item]
        ],
    )
    store.exchange_update(
        CollaborationConfigBase(
            name="id_collab", api=_IdKeyedAPI.get_name(), enabled=True
        ),
        create=True,
    )
    return store


def _bank_content(store: local_dbm.DBMStore, bank: str) -> t.Dict[int, t.Any]:
    """All content in a bank: id -> (config, signals)"""
    ids = {
        item.bank_content_id
        for item in store.bank_yield_content()
        if store.bank_content_get([item.bank_content_id])[0].bank.name == bank
    }
    signals = store.bank_content_get_signals(ids)
    return {c.id: (c, signals[c.id]) for c in store.bank_content_get(ids)}


def test_record_key_roundtrip() -> None:
    for key in ["abc", 123, ("pdq", "abc"), ("a", ("b", 1))]:
        as_str = local_dbm.record_key_to_str(key)
        assert isinstance(as_str, str)
        assert local_dbm.record_key_from_str(as_str) == key


def test_exchange_create_makes_bank(tmpdir: pathlib.Path) -> None:
    store = _make_store(tmpdir)
    store.exchange_update(_make_collab(), create=True)
    bank = store.get_bank("test_collab")
    assert bank is not None
    assert bank.enabled

    # Updating doesn't touch the bank
    store.exchange_update(_make_collab(), create=False)
    assert set(store.get_banks()) == {"test_collab"}

    # Never fetched, so default status
    status = store.exchange_get_fetch_status("test_collab")
    assert status.last_fetch_complete_ts is None
    assert status.fetched_items == 0


def test_exchange_create_bank_exists(tmpdir: pathlib.Path) -> None:
    store = _make_store(tmpdir)
    store.bank_update(_make_bank("test_collab"), create=True)
    with pytest.raises(ValueError, match="bank with that name already exists"):
        store.exchange_update(_make_collab(), create=True)
    # Nothing was written
    assert store.exchange_get("test_collab") is None


def test_exchange_create_bank_fails(tmpdir: pathlib.Path) -> None:
    store = _make_store(tmpdir)
    collab = _make_collab()
    with patch.object(store, "bank_update", side_effect=OSError("disk full")):
        store.exchange_update(collab, create=True)
    # The config is kept even though the bank couldn't be created
    assert store.exchange_get("test_collab") == collab
    assert store.get_bank("test_collab") is None

    # The next fetch creates it
    store.exchange_commit_fetch(
        collab, None, {("pdq", PDQ_A): FetchedSignalMetadata()}, NoCheckpointing()
    )
    assert store.get_bank("test_collab") is not None
    assert len(_bank_content(store, "test_collab")) == 1


def test_commit_fetch_populates_bank(tmpdir: pathlib.Path) -> None:
    store = _make_store(tmpdir)
    collab = _make_collab()
    store.exchange_update(collab, create=True)

    dat: dict = {
        ("pdq", PDQ_A): FetchedSignalMetadata(),
        ("video_md5", MD5_A): FetchedSignalMetadata(),
        ("pdq", "not a valid pdq"): FetchedSignalMetadata(),
    }
    store.exchange_commit_fetch(collab, None, dat, NoCheckpointing())

    # All records are stored, even the one without usable signals
    assert store.exchange_get_fetch_status("test_collab").fetched_items == 3

    content = _bank_content(store, "test_collab")
    assert sorted(tuple(signals.items()) for _, signals in content.values()) == [
        (("pdq", PDQ_A),),
        (("video_md5", MD5_A),),
    ]
    for cfg, signals in content.values():
        assert cfg.enabled
        # collab_metadata points back at the fetched record
        [(collab_name, [key_str])] = cfg.collab_metadata.items()
        assert collab_name == "test_collab"
        key = local_dbm.record_key_from_str(key_str)
        assert key == next(iter(signals.items()))
        assert store.exchange_get_data(collab_name, key) == FetchedSignalMetadata()

    assert store.get_current_index_build_target(PdqSignal).total_hash_count == 1
    assert store.get_current_index_build_target(VideoMD5Signal).total_hash_count == 1

    # Committing the same data again doesn't create duplicates
    store.exchange_commit_fetch(collab, NoCheckpointing(), dat, NoCheckpointing())
    assert _bank_content(store, "test_collab").keys() == content.keys()

    # Deleting a record removes its content
    store.exchange_commit_fetch(
        collab, NoCheckpointing(), {("pdq", PDQ_A): None}, NoCheckpointing()
    )
    assert [s for _, s in _bank_content(store, "test_collab").values()] == [
        {"video_md5": MD5_A}
    ]
    assert store.get_current_index_build_target(PdqSignal).total_hash_count == 0
    with pytest.raises(KeyError):
        store.exchange_get_data("test_collab", ("pdq", PDQ_A))


def test_commit_fetch_applies_merge(tmpdir: pathlib.Path) -> None:
    store = _make_id_keyed_store(tmpdir)
    collab = store.exchange_get("id_collab")
    assert collab is not None
    cp = NoCheckpointing()

    store.exchange_commit_fetch(
        collab, None, {"1": _IdKeyedRecord(pdq=PDQ_A, tags=["x"])}, cp
    )
    store.exchange_commit_fetch(
        collab, cp, {"1": _IdKeyedRecord(pdq=PDQ_A, tags=["y"])}, cp
    )
    # Merged with the stored value, rather than replaced
    assert store.exchange_get_data("id_collab", "1") == _IdKeyedRecord(
        pdq=PDQ_A, tags=["x", "y"]
    )

    # Merge returning None deletes the record and its content
    store.exchange_commit_fetch(collab, cp, {"1": _IdKeyedRecord(deleted=True)}, cp)
    with pytest.raises(KeyError):
        store.exchange_get_data("id_collab", "1")
    assert _bank_content(store, "id_collab") == {}
    assert store.exchange_get_fetch_status("id_collab").fetched_items == 0


def test_commit_fetch_signal_changes(tmpdir: pathlib.Path) -> None:
    store = _make_id_keyed_store(tmpdir)
    collab = store.exchange_get("id_collab")
    assert collab is not None
    cp = NoCheckpointing()

    store.exchange_commit_fetch(collab, None, {"1": _IdKeyedRecord(pdq=PDQ_A)}, cp)
    [(content_id, (_, signals))] = _bank_content(store, "id_collab").items()
    assert signals == {"pdq": PDQ_A}
    target_before = store.get_current_index_build_target(PdqSignal)

    # Signal changes: same content id, new signal, newer than the old target
    with patch("time.time", return_value=time.time() + 10):
        store.exchange_commit_fetch(collab, cp, {"1": _IdKeyedRecord(pdq=PDQ_B)}, cp)
    assert store.bank_content_get_signals([content_id]) == {content_id: {"pdq": PDQ_B}}
    target_after = store.get_current_index_build_target(PdqSignal)
    assert target_after.total_hash_count == 1
    assert target_after.last_item_timestamp > target_before.last_item_timestamp

    # No more usable signals: content removed, record kept
    store.exchange_commit_fetch(collab, cp, {"1": _IdKeyedRecord(tags=["z"])}, cp)
    assert _bank_content(store, "id_collab") == {}
    assert store.exchange_get_data("id_collab", "1") == _IdKeyedRecord(tags=["z"])

    # Signal comes back: new content
    store.exchange_commit_fetch(collab, cp, {"1": _IdKeyedRecord(pdq=PDQ_A)}, cp)
    [(new_content_id, (_, signals))] = _bank_content(store, "id_collab").items()
    assert signals == {"pdq": PDQ_A}
    assert new_content_id != content_id


def test_exchange_delete_removes_bank(tmpdir: pathlib.Path) -> None:
    store = _make_store(tmpdir)
    collab = _make_collab()
    store.exchange_update(collab, create=True)
    store.exchange_commit_fetch(
        collab, None, {("pdq", PDQ_A): FetchedSignalMetadata()}, NoCheckpointing()
    )
    assert len(_bank_content(store, "test_collab")) == 1

    store.exchange_delete("test_collab")
    assert store.get_banks() == {}
    assert list(store.bank_yield_content()) == []

    # Recreating starts from empty
    store.exchange_update(collab, create=True)
    assert _bank_content(store, "test_collab") == {}
    assert store.exchange_get_fetch_status("test_collab").fetched_items == 0


def test_exchange_clear_data(tmpdir: pathlib.Path) -> None:
    store = _make_store(tmpdir)
    collab = _make_collab()
    other = _make_collab("other_collab")
    store.exchange_update(collab, create=True)
    store.exchange_update(other, create=True)
    for c in (collab, other):
        store.exchange_commit_fetch(
            c, None, {("pdq", PDQ_A): FetchedSignalMetadata()}, NoCheckpointing()
        )
    store.exchange_start_fetch("test_collab")
    store.exchange_complete_fetch("test_collab", is_up_to_date=True, exception=False)

    store.exchange_clear_data("test_collab")

    # Config and (empty) bank kept
    assert store.exchange_get("test_collab") == collab
    assert store.get_bank("test_collab") is not None
    assert _bank_content(store, "test_collab") == {}
    # Data and status gone
    assert list(store.exchange_yield_data("test_collab")) == []
    assert store.exchange_get_fetch_checkpoint("test_collab") is None
    status = store.exchange_get_fetch_status("test_collab")
    assert status.fetched_items == 0
    assert status.last_fetch_complete_ts is None
    # Other collabs untouched
    assert len(_bank_content(store, "other_collab")) == 1
    assert store.exchange_get_fetch_status("other_collab").fetched_items == 1

    with pytest.raises(KeyError):
        store.exchange_clear_data("no_such_collab")


def test_exchange_yield_data(tmpdir: pathlib.Path) -> None:
    store = _make_store(tmpdir)
    collab = _make_collab()
    store.exchange_update(collab, create=True)
    assert list(store.exchange_yield_data("test_collab")) == []

    dat: dict = {
        ("pdq", PDQ_A): FetchedSignalMetadata(),
        ("video_md5", MD5_A): FetchedSignalMetadata(),
    }
    store.exchange_commit_fetch(collab, None, dat, NoCheckpointing())
    assert dict(store.exchange_yield_data("test_collab")) == dat

    id_keyed_dir = pathlib.Path(tmpdir) / "id_keyed"
    id_keyed_dir.mkdir()
    store2 = _make_id_keyed_store(id_keyed_dir)
    collab2 = store2.exchange_get("id_collab")
    assert collab2 is not None
    store2.exchange_commit_fetch(
        collab2, None, {"1": _IdKeyedRecord(pdq=PDQ_A)}, NoCheckpointing()
    )
    assert list(store2.exchange_yield_data("id_collab")) == [
        ("1", _IdKeyedRecord(pdq=PDQ_A))
    ]

    with pytest.raises(KeyError):
        list(store.exchange_yield_data("no_such_collab"))


def _dbm_backends() -> t.List[str]:
    """dbm backend modules available on this platform"""
    ret = []
    for name in ("dbm.gnu", "dbm.ndbm", "dbm.dumb", "dbm.sqlite3"):
        try:
            importlib.import_module(name)
        except ImportError:
            continue
        ret.append(name)
    return ret


@pytest.mark.parametrize("backend", _dbm_backends())
@pytest.mark.parametrize("batch_size", [1, 3, 100])
def test_iter_dbm_items(tmp_path: pathlib.Path, backend: str, batch_size: int) -> None:
    mod = importlib.import_module(backend)
    path = str(tmp_path / "db")

    def open_db() -> t.Any:
        return mod.open(path, "c")

    expected = {f"k{i}".encode(): f"v{i}".encode() for i in range(10)}
    with open_db() as db:
        for k, v in expected.items():
            db[k] = v

    seen = {}
    for k, v in local_dbm._iter_dbm_items(open_db, batch_size):
        # The db must not be held open while yielding (dbm.gnu locks it)
        with open_db() as db:
            assert db[k] == v
        assert k not in seen
        seen[k] = v
    assert seen == expected

    assert (
        list(
            local_dbm._iter_dbm_items(
                lambda: mod.open(str(tmp_path / "empty"), "c"), batch_size
            )
        )
        == []
    )


def test_iter_gdbm_items_last_key_deleted(tmp_path: pathlib.Path) -> None:
    gnu = pytest.importorskip("dbm.gnu")
    path = str(tmp_path / "db")

    def open_db() -> t.Any:
        return gnu.open(path, "c")

    with open_db() as db:
        for i in range(4):
            db[f"k{i}".encode()] = b"v"

    it = local_dbm._iter_dbm_items(open_db, batch_size=2)
    next(it)
    last, _ = next(it)
    with open_db() as db:
        del db[last]
    with pytest.raises(RuntimeError, match="deleted mid-iteration"):
        next(it)


def test_exchange_delete_order(tmpdir: pathlib.Path) -> None:
    """Teardown is status, data, bank, config: interrupting leaves the later ones"""
    store = _make_store(tmpdir)
    collab = _make_collab()
    store.exchange_update(collab, create=True)

    def fetch() -> None:
        store.exchange_start_fetch("test_collab")
        store.exchange_commit_fetch(
            collab, None, {("pdq", PDQ_A): FetchedSignalMetadata()}, NoCheckpointing()
        )
        assert store.exchange_get_fetch_checkpoint("test_collab") is not None

    fetch()
    # Fails clearing data: only the status (and checkpoint) are gone
    with patch.object(local_dbm, "_clear_data", side_effect=OSError("boom")):
        with pytest.raises(OSError):
            store.exchange_delete("test_collab")
    assert store.exchange_get_fetch_checkpoint("test_collab") is None
    assert store.exchange_get_fetch_status("test_collab").fetched_items == 1
    assert len(_bank_content(store, "test_collab")) == 1
    assert store.exchange_get("test_collab") == collab

    fetch()
    # Fails deleting the bank: status and data are gone, bank and config remain
    with patch.object(store, "bank_delete", side_effect=OSError("boom")):
        with pytest.raises(OSError):
            store.exchange_delete("test_collab")
    assert store.exchange_get_fetch_checkpoint("test_collab") is None
    assert store.exchange_get_fetch_status("test_collab").fetched_items == 0
    assert store.get_bank("test_collab") is not None
    assert store.exchange_get("test_collab") == collab

    store.exchange_delete("test_collab")
    assert store.get_bank("test_collab") is None
    assert store.exchange_get("test_collab") is None
