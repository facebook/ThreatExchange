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
import datetime

from OpenMediaMatch.storage.interface import BankConfig, BankContentConfig

from threatexchange.exchanges.collab_config import CollaborationConfigBase
from threatexchange.exchanges.signal_exchange_api import (
    TSignalExchangeAPICls,
    SignalExchangeAPI,
    TCollabConfig,
)
from threatexchange.signal_type.index import SignalTypeIndex
from threatexchange.utils import dataclass_json

import flask_sqlalchemy
from sqlalchemy import String, Text, ForeignKey, JSON, LargeBinary
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


class Bank(db.Model):  # type: ignore[name-defined]
    __tablename__ = "bank"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    enabled_ratio: Mapped[float] = mapped_column(default=1.0)

    content: Mapped[t.List["BankContent"]] = relationship(
        back_populates="bank", cascade="all, delete"
    )

    def as_storage_iface_cls(self) -> BankConfig:
        return BankConfig(self.name, self.enabled_ratio)

    @classmethod
    def from_storage_iface_cls(cls, cfg: BankConfig) -> t.Self:
        return cls(name=cfg.name, enabled_ratio=cfg.matching_enabled_ratio)

    @validates("name")
    def validate_name(self, _key: str, name: str) -> str:
        if not re.fullmatch("[A-Z_][A-Z0-9_]*", name):
            raise ValueError("Bank names must be UPPER_WITH_UNDERSCORE")
        return name


class BankContent(db.Model):  # type: ignore[name-defined]
    __tablename__ = "bank_content"

    id: Mapped[int] = mapped_column(primary_key=True)
    bank_id: Mapped[int] = mapped_column(ForeignKey("bank.id"))
    bank: Mapped[Bank] = relationship(back_populates="content")

    # Should we store the content type as well?

    disable_until_ts: Mapped[int] = mapped_column(default=BankContentConfig.ENABLED)
    original_content_uri: Mapped[t.Optional[str]]

    signals: Mapped[t.List["ContentSignal"]] = relationship(cascade="all, delete")

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
        ForeignKey("bank_content.id"), primary_key=True
    )
    signal_type: Mapped[str] = mapped_column(primary_key=True)
    signal_val: Mapped[str] = mapped_column(Text)


class CollaborationConfig(db.Model):  # type: ignore[name-defined]
    id: Mapped[int] = mapped_column(primary_key=True)
    # These three fields are also in typed_config, but exposing them
    # allows for selecting them from the database layer
    name: Mapped[str] = mapped_column(String(255), unique=True)
    api_cls: Mapped[str] = mapped_column(String(255))
    fetching_enabled: Mapped[bool] = mapped_column(default=True)
    # Someday, we want writeback columns
    # report_seen: Mapped[bool] = mapped_column(default=True)
    # report_true_positive = mapped_column(default=True)
    # report_false_positive = mapped_column(default=True)

    # This is the dacite-serialized version of the typed
    # CollaborationConfig.
    typed_config: Mapped[t.Dict[str, t.Any]] = mapped_column(JSON)

    def set_typed_config(self, cfg: CollaborationConfigBase) -> t.Self:
        self.name = cfg.name
        self.fetching_enabled = cfg.enabled
        self.api_cls = cfg.api
        self.typed_config = dataclass_json.dataclass_dump_dict(cfg)
        return self

    def as_storage_iface_cls(
        self, exchange_types: t.Dict[str, TSignalExchangeAPICls]
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

    @validates("name")
    def validate_name(self, _key: str, name: str) -> str:
        if not re.fullmatch("[A-Z_]+", name):
            raise ValueError("Collaboration names must be UPPER_WITH_UNDERSCORE")
        return name


class SignalIndex(db.Model):  # type: ignore[name-defined]
    """
    Table for storing the large indices
    """

    id: Mapped[int] = mapped_column(primary_key=True)
    signal_type: Mapped[str]
    serialized_index: Mapped[bytes] = mapped_column(LargeBinary)
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


class SignalTypeOverride(db.Model):  # type: ignore[name-defined]
    """
    Stores signal types and whether they are enabled or disabled.
    By default, any type not in this database is
    """

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    enabled_ratio: Mapped[float] = mapped_column(default=1.0)
