# Copyright (c) Meta Platforms, Inc. and affiliates.

import pathlib
import pytest

from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.exchanges.fetch_state import NoCheckpointing
from threatexchange.exchanges.impl.static_sample import StaticSampleSignalExchangeAPI
from threatexchange.exchanges.impl.fb_threatexchange_api import (
    FBThreatExchangeCollabConfig,
    FBThreatExchangeSignalExchangeAPI,
)
from threatexchange.storage import interfaces as iface
from threatexchange.storage import local_dbm


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
    cfg = iface.SignalExchangeAPIConfig(api_cls=StaticSampleSignalExchangeAPI)  # type: ignore[arg-type]
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

from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal


def _make_bank(name: str = "TEST_BANK", ratio: float = 1.0) -> iface.BankConfig:
    return iface.BankConfig(name=name, matching_enabled_ratio=ratio)


def test_bank_create_get_delete(tmpdir: pathlib.Path) -> None:
    store = local_dbm.DBMStore(pathlib.Path(tmpdir))

    # Initially empty
    assert store.get_banks() == {}
    assert store.get_bank("TEST_BANK") is None

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
    assert store.get_bank("TEST_BANK").matching_enabled_ratio == 0.5  # type: ignore[union-attr]

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
