# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
SQLAlchemy backed relational data.

We are trying to make all the persistent data accessed instead
through the storage interface. However, during development, that's
slower than just slinging sql on the tables, so you may see direct
references which are meant to be reaped at some future time.
"""

import datetime
import io
import json
import re
import logging
import tempfile
import time
import typing as t
import os

from flask import current_app
import flask_sqlalchemy
from sqlalchemy import (
    String,
    Text,
    ForeignKey,
    JSON,
    LargeBinary,
    Index,
    UniqueConstraint,
    BigInteger,
    event,
)
from sqlalchemy.dialects.postgresql import OID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    DeclarativeBase,
    relationship,
    validates,
)
from sqlalchemy.types import DateTime
from sqlalchemy.sql import func

from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.exchanges.signal_exchange_api import (
    TSignalExchangeAPICls,
    SignalExchangeAPI,
    TCollabConfig,
)
from threatexchange.exchanges.fetch_state import FetchCheckpointBase
from threatexchange.signal_type.index import SignalTypeIndex
from threatexchange.utils import dataclass_json

from OpenMediaMatch.utils.time_utils import duration_to_human_str
from OpenMediaMatch.storage.interface import (
    BankConfig,
    BankContentConfig,
    FetchStatus,
    SignalTypeIndexBuildCheckpoint,
    BankContentIterationItem,
)


class Base(DeclarativeBase):
    pass


# Initializing this at import time seems to be the only correct
# way to do this
db = flask_sqlalchemy.SQLAlchemy(model_class=Base)


def _bank_name_ok(name: str) -> bool:
    return bool(re.fullmatch("[A-Z_][A-Z0-9_]*", name))


class Bank(db.Model):  # type: ignore[name-defined]
    __tablename__ = "bank"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    enabled_ratio: Mapped[float] = mapped_column(default=1.0)

    content: Mapped[t.List["BankContent"]] = relationship(
        back_populates="bank", cascade="all, delete"
    )

    import_from_exchange_id: Mapped[t.Optional[int]] = mapped_column(
        ForeignKey("exchange.id", ondelete="CASCADE"),
        default=None,
        unique=True,
    )
    import_from_exchange: Mapped[t.Optional["ExchangeConfig"]] = relationship(
        foreign_keys=[import_from_exchange_id],
        single_parent=True,
    )

    def as_storage_iface_cls(self) -> BankConfig:
        return BankConfig(self.name, self.enabled_ratio)

    @classmethod
    def from_storage_iface_cls(cls, cfg: BankConfig) -> t.Self:
        return cls(name=cfg.name, enabled_ratio=cfg.matching_enabled_ratio)

    @validates("name")
    def validate_name(self, _key: str, name: str) -> str:
        if not _bank_name_ok(name):
            raise ValueError("Bank names must be UPPER_WITH_UNDERSCORE")
        return name


class BankContent(db.Model):  # type: ignore[name-defined]
    __tablename__ = "bank_content"

    id: Mapped[int] = mapped_column(primary_key=True)
    bank_id: Mapped[int] = mapped_column(
        ForeignKey(Bank.id, ondelete="CASCADE"), index=True
    )
    bank: Mapped[Bank] = relationship(back_populates="content")

    imported_from_id: Mapped[t.Optional[int]] = mapped_column(
        ForeignKey("exchange_data.id", ondelete="CASCADE"),
        default=None,
        unique=True,
    )
    imported_from: Mapped[t.Optional["ExchangeData"]] = relationship(
        back_populates="bank_content",
        foreign_keys=[imported_from_id],
    )

    # Should we store the content type as well?

    disable_until_ts: Mapped[int] = mapped_column(default=BankContentConfig.ENABLED)
    original_content_uri: Mapped[t.Optional[str]]

    signals: Mapped[t.List["ContentSignal"]] = relationship(
        back_populates="content", cascade="all, delete"
    )

    def as_storage_iface_cls(self) -> BankContentConfig:
        return BankContentConfig(
            self.id,
            disable_until_ts=self.disable_until_ts,
            collab_metadata={},
            original_media_uri=None,
            bank=self.bank.as_storage_iface_cls(),
        )


class ContentSignal(db.Model):  # type: ignore[name-defined]
    content_id: Mapped[int] = mapped_column(
        ForeignKey(BankContent.id, ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    content: Mapped[BankContent] = relationship(back_populates="signals")

    signal_type: Mapped[str] = mapped_column(primary_key=True)
    signal_val: Mapped[str] = mapped_column(Text)

    create_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index(
            "incremental_index_build_idx", "signal_type", "create_time", "content_id"
        ),
    )

    def as_iteration_item(self) -> BankContentIterationItem:
        return BankContentIterationItem(
            signal_type_name=self.signal_type,
            signal_val=self.signal_val,
            bank_content_id=self.content_id,
            bank_content_timestamp=int(self.create_time.timestamp()),
        )


class ExchangeConfig(db.Model):  # type: ignore[name-defined]
    __tablename__ = "exchange"

    id: Mapped[int] = mapped_column(primary_key=True)
    # These three fields are also in typed_config, but exposing them
    # allows for selecting them from the database layer
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    api_cls: Mapped[str] = mapped_column(String(255))
    retain_api_data: Mapped[bool] = mapped_column(default=False)
    fetching_enabled: Mapped[bool] = mapped_column(default=True)
    retain_data_with_unknown_signal_types: Mapped[bool] = mapped_column(default=False)
    # Someday, we want writeback columns
    # report_seen: Mapped[bool] = mapped_column(default=False)
    # report_true_positive = mapped_column(default=False)
    # report_false_positive = mapped_column(default=False)

    # This is the dacite-serialized version of the typed
    # CollaborationConfig.
    typed_config: Mapped[t.Dict[str, t.Any]] = mapped_column(JSON)

    fetch_status: Mapped[t.Optional["ExchangeFetchStatus"]] = relationship(
        "ExchangeFetchStatus",
        back_populates="collab",
        cascade="all, delete",
        passive_deletes=True,
    )

    import_bank: Mapped[Bank] = relationship(
        "Bank",
        cascade="all, delete",
        back_populates="import_from_exchange",
        uselist=False,
    )

    def set_typed_config(self, cfg: CollaborationConfigBase) -> t.Self:
        self.name = cfg.name
        self.fetching_enabled = cfg.enabled
        self.api_cls = cfg.api
        # This foolishness is because dataclass_dump handles more types
        # than sqlalchemy JSON is willing to, so we "cast" to simple json
        as_json_str = dataclass_json.dataclass_dumps(cfg)
        self.typed_config = json.loads(as_json_str)
        return self

    def as_storage_iface_cls(
        self, exchange_types: t.Mapping[str, TSignalExchangeAPICls]
    ) -> CollaborationConfigBase:
        exchange_cls = exchange_types.get(self.api_cls)
        if exchange_cls is None:
            # If this is None, it means we either serialized it wrong, or
            # we changed which exchanges were valid between storing and
            # fetching.
            # We could throw an exception here, but maybe instead we just
            # return it stripped and let the application figure out what to do
            # with an invalid API cls.
            return CollaborationConfigBase(
                name=self.name, api=self.api_cls, enabled=self.fetching_enabled
            )
        return self.as_storage_iface_cls_typed(exchange_cls)

    def as_storage_iface_cls_typed(
        self,
        exchange_cls: t.Type[
            SignalExchangeAPI[TCollabConfig, t.Any, t.Any, t.Any, t.Any]
        ],
    ) -> TCollabConfig:
        cls = exchange_cls.get_config_cls()
        # This looks like it should be typed correctly, but too complicated
        # mypy
        return dataclass_json.dataclass_load_dict(
            self.typed_config, cls
        )  # type: ignore[return-value]

    def as_checkpoint(
        self, exchange_types: t.Mapping[str, TSignalExchangeAPICls]
    ) -> t.Optional[FetchCheckpointBase]:
        fetch_status = self.fetch_status
        if fetch_status is None:
            return None
        api_cls = exchange_types.get(self.api_cls)
        if api_cls is None:
            return None
        return fetch_status.as_checkpoint(api_cls)

    def status_as_storage_iface_cls(
        self, exchange_types: t.Mapping[str, TSignalExchangeAPICls]
    ) -> FetchStatus:
        fetch_status = self.fetch_status
        if fetch_status is None:
            return FetchStatus.get_default()
        return fetch_status.as_storage_iface_cls()

    @validates("name")
    def validate_name(self, _key: str, name: str) -> str:
        if _bank_name_ok(name):
            return name
        raise ValueError("Collaboration names must be UPPER_WITH_UNDERSCORE")


class ExchangeFetchStatus(db.Model):  # type: ignore[name-defined]
    collab_id: Mapped[int] = mapped_column(
        ForeignKey(ExchangeConfig.id, ondelete="CASCADE"), primary_key=True
    )
    collab: Mapped["ExchangeConfig"] = relationship(
        back_populates="fetch_status",
        uselist=False,
        single_parent=True,
    )

    running_fetch_start_ts: Mapped[t.Optional[int]] = mapped_column(BigInteger)
    # I tried to make this an enum, but postgres enums malfunction with drop_all()
    last_fetch_succeeded: Mapped[t.Optional[bool]]
    last_fetch_complete_ts: Mapped[t.Optional[int]] = mapped_column(BigInteger)

    is_up_to_date: Mapped[bool] = mapped_column(default=False)

    # Storing the ts separately means we can check the timestamp without deserializing
    # the checkpoint
    checkpoint_ts: Mapped[t.Optional[int]] = mapped_column(BigInteger)
    checkpoint_json: Mapped[t.Optional[t.Dict[str, t.Any]]] = mapped_column(JSON)

    def as_checkpoint(
        self, api_cls: t.Optional[TSignalExchangeAPICls]
    ) -> t.Optional[FetchCheckpointBase]:
        if api_cls is None:
            return None
        checkpoint_json = self.checkpoint_json
        if checkpoint_json is None:
            return None
        return dataclass_json.dataclass_load_dict(
            checkpoint_json, api_cls.get_checkpoint_cls()
        )

    def set_checkpoint(self, checkpoint: FetchCheckpointBase) -> None:
        self.checkpoint_json = dataclass_json.dataclass_dump_dict(checkpoint)
        self.checkpoint_ts = checkpoint.get_progress_timestamp()

    def as_storage_iface_cls(self) -> FetchStatus:
        return FetchStatus(
            checkpoint_ts=self.checkpoint_ts,
            running_fetch_start_ts=self.running_fetch_start_ts,
            last_fetch_complete_ts=self.last_fetch_complete_ts,
            last_fetch_succeeded=self.last_fetch_succeeded,
            up_to_date=self.is_up_to_date,
            fetched_items=0,
        )


class ExchangeData(db.Model):  # type: ignore[name-defined]
    __tablename__ = "exchange_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    collab_id: Mapped[int] = mapped_column(
        ForeignKey(ExchangeConfig.id, ondelete="CASCADE"), index=True
    )

    fetch_id: Mapped[str] = mapped_column(Text)
    # Making this optional allows us to store only the summary in the future,
    # but might be a premature optimization
    pickled_fetch_signal_metadata: Mapped[t.Optional[bytes]] = mapped_column(
        LargeBinary
    )
    fetched_metadata_summary: Mapped[t.List[t.Any]] = mapped_column(JSON, default=list)

    bank_content: Mapped[t.Optional[BankContent]] = relationship(
        back_populates="imported_from",
        cascade="all, delete",
        passive_deletes=True,
        uselist=False,
    )

    # Whether this has been matched by this instance of OMM
    matched: Mapped[bool] = mapped_column(default=False)
    # null = not verified; true = positive class; false = negative class
    verification_result: Mapped[t.Optional[bool]] = mapped_column(default=None)

    collab: Mapped["ExchangeConfig"] = relationship()

    __table_args__ = (UniqueConstraint("collab_id", "fetch_id"),)


class SignalIndex(db.Model):  # type: ignore[name-defined]
    """
    Table for storing the large indices and their build status.
    """

    id: Mapped[int] = mapped_column(primary_key=True)
    signal_type: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    signal_count: Mapped[int]
    updated_to_id: Mapped[int]
    updated_to_ts: Mapped[int] = mapped_column(BigInteger)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=db.func.now()
    )

    serialized_index_large_object_oid: Mapped[int | None] = mapped_column(OID)

    def commit_signal_index(
        self, index: SignalTypeIndex[int], checkpoint: SignalTypeIndexBuildCheckpoint
    ) -> t.Self:
        self.updated_to_id = checkpoint.last_item_id
        self.updated_to_ts = checkpoint.last_item_timestamp
        self.signal_count = checkpoint.total_hash_count

        serialize_start_time = time.time()
        with tempfile.NamedTemporaryFile("wb", delete=False) as tmpfile:
            self._log("serializing index to tmpfile %s", tmpfile.name)
            index.serialize(t.cast(t.BinaryIO, tmpfile.file))
            size = tmpfile.tell()
        self._log(
            "finished writing to tmpfile, %d signals %d bytes - %s",
            self.signal_count,
            size,
            duration_to_human_str(int(time.time() - serialize_start_time)),
        )

        store_start_time = time.time()
        # Deep dark magic - direct access postgres large object API
        raw_conn = db.engine.raw_connection()
        l_obj = raw_conn.lobject(0, "wb", 0, tmpfile.name)  # type: ignore[attr-defined]
        self._log(
            "imported tmpfile as lobject oid %d - %s",
            l_obj.oid,
            duration_to_human_str(int(time.time() - store_start_time)),
        )
        if self.serialized_index_large_object_oid is not None:
            old_obj = raw_conn.lobject(self.serialized_index_large_object_oid, "n")  # type: ignore[attr-defined]
            self._log("deallocating old lobject %d", old_obj.oid)
            old_obj.unlink()

        self.serialized_index_large_object_oid = l_obj.oid
        db.session.add(self)
        raw_conn.commit()

        try:
            os.unlink(tmpfile.name)
        except Exception:
            self._log(
                "failed to clean up tmpfile %s!", tmpfile.name, level=logging.ERROR
            )
        self._log("cleaned up tmpfile")

        return self

    def load_signal_index(self) -> SignalTypeIndex[int]:
        oid = self.serialized_index_large_object_oid
        assert oid is not None
        # If we were being fully proper, we would get the SignalType
        # class and use that index to compare them. However, every existing
        # index as of 10/2/2023 is using pickle, which will produce the right
        # class no matter which interface we call it on.
        # I'm sorry future debugger finding this comment.
        load_start_time = time.time()
        raw_conn = db.engine.raw_connection()
        l_obj = raw_conn.lobject(oid, "rb")  # type: ignore[attr-defined]

        with tempfile.NamedTemporaryFile("rb") as tmpfile:
            self._log("importing lobject oid %d to tmpfile %s", l_obj.oid, tmpfile.name)
            l_obj.export(tmpfile.name)
            tmpfile.seek(0, io.SEEK_END)
            self._log(
                "loaded %d bytes to tmpfile - %s",
                tmpfile.tell(),
                duration_to_human_str(int(time.time() - load_start_time)),
            )
            tmpfile.seek(0)

            deserialize_start = time.time()
            index = t.cast(
                SignalTypeIndex[int],
                SignalTypeIndex.deserialize(t.cast(t.BinaryIO, tmpfile.file)),
            )
            self._log(
                "deserialized - %s",
                duration_to_human_str(int(time.time() - deserialize_start)),
            )
        return index

    def as_checkpoint(self) -> SignalTypeIndexBuildCheckpoint:
        return SignalTypeIndexBuildCheckpoint(
            last_item_id=self.updated_to_id,
            last_item_timestamp=self.updated_to_ts,
            total_hash_count=self.signal_count,
        )

    def _log(self, msg: str, *args: t.Any, level: int = logging.DEBUG) -> None:
        current_app.logger.log(level, f"Index[%s] {msg}", self.signal_type, *args)


@event.listens_for(SignalIndex, "after_delete")
def _remove_large_object_after_delete(_, connection, signal_index: SignalIndex) -> None:
    """
    Hopefully we don't need to rely on this, but attempt to prevent orphaned large objects.
    """
    raw_connection = connection.connection
    l_obj = raw_connection.lobject(signal_index.serialized_index_large_object_oid, "n")
    l_obj.unlink()
    raw_connection.commit()


class SignalTypeOverride(db.Model):  # type: ignore[name-defined]
    """
    Stores signal types and whether they are enabled or disabled.

    By default, any type not in this database is disabled.
    """

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    enabled_ratio: Mapped[float] = mapped_column(default=1.0)


class ExchangeAPIConfig(db.Model):  # type: ignore[name-defined]
    """
    Store any per-API config we might need.
    """

    id: Mapped[int] = mapped_column(primary_key=True)
    api: Mapped[str] = mapped_column(unique=True)
    # If the credentials can't be produced at docker build time, here's a
    # backup location to store them. You'll have to modify the OMM code to
    # use them how your API expects if it's not one of the natively supported
    # Exchange types.
    # This should correspond to threatexchange.exchanges.authCredentialHelper
    # object
    defaul_credentials_json: Mapped[t.Dict[str, t.Any]] = mapped_column(JSON)
