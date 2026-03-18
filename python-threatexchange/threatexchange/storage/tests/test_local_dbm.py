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
