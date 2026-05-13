# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t
from unittest.mock import patch, MagicMock
from flask import Flask
from sqlalchemy import select, and_

from threatexchange.exchanges.signal_exchange_api import TSignalExchangeAPICls
from threatexchange.exchanges.impl.static_sample import StaticSampleSignalExchangeAPI
from threatexchange.exchanges.impl.fb_threatexchange_api import (
    FBThreatExchangeSignalExchangeAPI,
)
from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.signal_type.signal_base import TrivialSignalTypeIndex
from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal

from OpenMediaMatch.storage.postgres import database
from threatexchange.storage.interfaces import SignalTypeIndexBuildCheckpoint
from OpenMediaMatch.tests.utils import app


def test_store_collab_config(app: Flask) -> None:
    existing = (
        database.db.session.execute(select(database.ExchangeConfig)).scalars().all()
    )
    assert existing == []

    all_exchange_apis: t.List[TSignalExchangeAPICls] = [
        StaticSampleSignalExchangeAPI,  # type: ignore[list-item]
        FBThreatExchangeSignalExchangeAPI,  # type: ignore[list-item]  # another mypy corner case
    ]
    exchange_apis = {ex.get_name(): ex for ex in all_exchange_apis}

    typed_config_default = CollaborationConfigBase(
        name="BASIC",
        api=StaticSampleSignalExchangeAPI.get_name(),
        enabled=True,
    )
    extended_cls = FBThreatExchangeSignalExchangeAPI.get_config_cls()
    typed_config_extended = extended_cls(
        name="EXTENDED",
        privacy_group=1234567,
        enabled=True,
    )

    database.db.session.add(
        database.ExchangeConfig(
            import_bank=database.Bank(name="BASIC_BANK")
        ).set_typed_config(typed_config_default)
    )
    database.db.session.add(
        database.ExchangeConfig(
            import_bank=database.Bank(name="EXTENDED_BANK")
        ).set_typed_config(typed_config_extended)
    )
    database.db.session.commit()

    from_db = (
        database.db.session.execute(select(database.ExchangeConfig)).scalars().all()
    )

    assert len(from_db) == 2
    by_name = {c.name: c.as_storage_iface_cls(exchange_apis) for c in from_db}

    for config in (typed_config_default, typed_config_extended):
        assert config == by_name.get(config.name)


def test_store_index(app: Flask) -> None:
    # We use Trivial index here because it's possible to compare the contents
    # In theory, if it works for this one, it works for any of them
    content = [("a", 1), ("a", 2), ("b", 3), ("c", 4)]
    index = TrivialSignalTypeIndex.build(content)
    assert index.state == {"a": [1, 2], "b": [3], "c": [4]}

    database.db.session.add(
        database.SignalIndex(
            signal_type="test",
            updated_to_ts=12345,
            updated_to_id=5678,
            signal_count=len(content),
        ).commit_signal_index(index, SignalTypeIndexBuildCheckpoint.get_empty())
    )
    database.db.session.commit()
    database.db.session.query()
    db_record = database.db.session.execute(
        select(database.SignalIndex).where(database.SignalIndex.signal_type == "test")
    ).scalar_one()

    deserialized_index = t.cast(TrivialSignalTypeIndex, db_record.load_signal_index())

    assert index.__class__ == deserialized_index.__class__
    assert index.state == deserialized_index.state


def test_store_index_updated_at(app: Flask) -> None:
    db_record = database.db.session.execute(
        select(database.SignalIndex).where(database.SignalIndex.signal_type == "test")
    ).one_or_none()
    content = [("a", 1), ("a", 2), ("b", 3), ("c", 4)]
    index = TrivialSignalTypeIndex.build(content)

    database.db.session.add(
        database.SignalIndex(
            signal_type="test",
            updated_to_ts=1234,
            updated_to_id=5678,
            signal_count=len(content),
        ).commit_signal_index(index, SignalTypeIndexBuildCheckpoint.get_empty())
    )
    database.db.session.commit()
    db_record = database.db.session.execute(
        select(database.SignalIndex).where(database.SignalIndex.signal_type == "test")
    ).scalar_one()
    initial_time = db_record.updated_at

    content = [("a", 1), ("a", 2), ("b", 3), ("c", 4), ("d", 5)]
    index = TrivialSignalTypeIndex.build(content)

    # Update index to trigger time change
    db_record.commit_signal_index(index, SignalTypeIndexBuildCheckpoint.get_empty())
    db_record = database.db.session.execute(
        select(database.SignalIndex).where(database.SignalIndex.signal_type == "test")
    ).scalar_one()

    deserialized_index = t.cast(TrivialSignalTypeIndex, db_record.load_signal_index())

    assert index.__class__ == deserialized_index.__class__
    assert index.state == deserialized_index.state
    assert initial_time != db_record.updated_at


def test_store_content(app: Flask) -> None:
    db = database.db
    sesh = db.session

    bank = database.Bank(name="TEST_STORE_CONTENT")
    sesh.add(bank)
    content = database.BankContent(bank=bank)
    sesh.add(content)
    sesh.flush()
    hash1 = database.ContentSignal(
        content_id=content.id,
        signal_type=PdqSignal.get_name(),
        signal_val=PdqSignal.get_examples()[0],
    )
    sesh.add(hash1)
    hash2 = database.ContentSignal(
        content_id=content.id,
        signal_type=VideoMD5Signal.get_name(),
        signal_val=VideoMD5Signal.get_examples()[0],
    )
    sesh.add(hash2)
    sesh.commit()

    hash1_val = sesh.execute(
        select(database.ContentSignal).where(
            and_(
                database.ContentSignal.content_id == content.id,
                database.ContentSignal.signal_type == PdqSignal.get_name(),
            )
        )
    ).scalar_one()
    assert PdqSignal.get_examples()[0] == hash1_val.signal_val


def _create_index_record() -> database.SignalIndex:
    """Helper to create and commit a SignalIndex record for testing."""
    content = [("a", 1), ("b", 2)]
    index = TrivialSignalTypeIndex.build(content)
    record = database.SignalIndex(
        signal_type="read_replica_test",
        updated_to_ts=1,
        updated_to_id=1,
        signal_count=len(content),
    ).commit_signal_index(index, SignalTypeIndexBuildCheckpoint.get_empty())
    database.db.session.add(record)
    database.db.session.commit()
    return database.db.session.execute(
        select(database.SignalIndex).where(
            database.SignalIndex.signal_type == "read_replica_test"
        )
    ).scalar_one()


def test_load_signal_index_uses_read_engine(app: Flask) -> None:
    db_record = _create_index_record()
    read_engine = database.db.engines["read"]

    with patch.object(read_engine, "raw_connection", wraps=read_engine.raw_connection) as mock_conn:
        db_record.load_signal_index()
        mock_conn.assert_called_once()


def test_index_lobj_exists_uses_read_session_by_default(app: Flask) -> None:
    db_record = _create_index_record()

    with patch("OpenMediaMatch.storage.postgres.database.get_read_session") as mock_get:
        mock_session = MagicMock()
        mock_session.execute.return_value.scalar_one.return_value = 1
        mock_get.return_value = mock_session

        result = db_record.index_lobj_exists()

        mock_get.assert_called_once()
        assert result is True


def test_index_lobj_exists_uses_provided_session(app: Flask) -> None:
    db_record = _create_index_record()
    mock_session = MagicMock()
    mock_session.execute.return_value.scalar_one.return_value = 1

    result = db_record.index_lobj_exists(session=mock_session)

    mock_session.execute.assert_called_once()
    assert result is True
