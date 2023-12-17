# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
SQLAlchemy backed relational data.

We are trying to make all the persistent data accessed instead
through the storage interface. However, during development, that's
slower than just slinging sql on the tables, so you may see direct
references which are meant to be reaped at some future time.
"""

import io
import typing as t
import re
import json
import datetime

from OpenMediaMatch.storage.interface import (
    BankConfig,
    BankContentConfig,
    FetchStatus,
    SignalTypeIndexBuildCheckpoint,
    BankContentIterationItem,
)

from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.exchanges.signal_exchange_api import (
    TSignalExchangeAPICls,
    SignalExchangeAPI,
    TCollabConfig,
)
from threatexchange.exchanges.fetch_state import FetchCheckpointBase
from threatexchange.signal_type.index import SignalTypeIndex
from threatexchange.utils import dataclass_json

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
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    DeclarativeBase,
    relationship,
    validates,
)
from sqlalchemy.types import DateTime
from sqlalchemy.sql import func


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

    import_from_exchange: Mapped[t.Optional["CollaborationConfig"]] = relationship(
        back_populates="import_bank", cascade="all, delete"
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
    bank_id: Mapped[int] = mapped_column(ForeignKey(Bank.id), index=True)
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


# TODO: Rename to Exchange
class CollaborationConfig(db.Model):  # type: ignore[name-defined]
    __tablename__ = "exchange"

    id: Mapped[int] = mapped_column(primary_key=True)
    # These three fields are also in typed_config, but exposing them
    # allows for selecting them from the database layer
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    api_cls: Mapped[str] = mapped_column(String(255))
    fetching_enabled: Mapped[bool] = mapped_column(default=True)
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

    import_bank_id: Mapped[int] = mapped_column(ForeignKey(Bank.id), unique=True)
    import_bank: Mapped[Bank] = relationship("Bank", cascade="all, delete")

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
        ForeignKey(CollaborationConfig.id, ondelete="CASCADE"), primary_key=True
    )
    collab: Mapped["CollaborationConfig"] = relationship(
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
        ForeignKey(CollaborationConfig.id, ondelete="CASCADE"), index=True
    )

    fetch_id: Mapped[str] = mapped_column(Text)
    pickled_original_fetch_data: Mapped[t.Optional[bytes]] = mapped_column(LargeBinary)
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

    collab: Mapped["CollaborationConfig"] = relationship()

    __table_args__ = (UniqueConstraint("collab_id", "fetch_id"),)


class SignalIndex(db.Model):  # type: ignore[name-defined]
    """
    Table for storing the large indices and their build status.
    """

    id: Mapped[int] = mapped_column(primary_key=True)
    signal_type: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    serialized_index: Mapped[bytes] = mapped_column(LargeBinary)
    signal_count: Mapped[int]
    updated_to_id: Mapped[int]
    updated_to_ts: Mapped[int] = mapped_column(BigInteger)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=db.func.now()
    )

    def serialize_index(self, index: SignalTypeIndex[int]) -> t.Self:
        buffer = io.BytesIO()
        index.serialize(buffer)
        self.serialized_index = buffer.getvalue()
        return self

    def deserialize_index(self) -> SignalTypeIndex[int]:
        # If we were being fully proper, we would get the SignalType
        # class and use that index to compare them. However, every existing
        # index as of 10/2/2023 is using pickle, which will produce the right
        # class no matter which interface we call it on.
        # I'm sorry future debugger finding this comment.
        return SignalTypeIndex.deserialize(io.BytesIO(self.serialized_index))

    def update_checkpoint(self, checkpoint: SignalTypeIndexBuildCheckpoint) -> t.Self:
        self.updated_to_id = checkpoint.last_item_id
        self.updated_to_ts = checkpoint.last_item_timestamp
        self.signal_count = checkpoint.total_hash_count
        return self

    def as_checkpoint(self) -> SignalTypeIndexBuildCheckpoint:
        return SignalTypeIndexBuildCheckpoint(
            last_item_id=self.updated_to_id,
            last_item_timestamp=self.updated_to_ts,
            total_hash_count=self.signal_count,
        )


class SignalTypeOverride(db.Model):  # type: ignore[name-defined]
    """
    Stores signal types and whether they are enabled or disabled.

    By default, any type not in this database is disabled.
    """

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    enabled_ratio: Mapped[float] = mapped_column(default=1.0)
