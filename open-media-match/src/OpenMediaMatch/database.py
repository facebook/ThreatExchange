# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
SQLAlchemy backed relational data.

We are trying to make all the persistent data accessed instead
through the storage interface. However, during development, that's
slower than just slinging sql on the tables, so you may see direct
references which are meant to be reaped at some future time.
"""

import typing as t

from dataclasses import dataclass
from OpenMediaMatch.storage.interface import BankConfig, BankContentConfig

import flask_sqlalchemy
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


import sqlalchemy.types as dbtypes
from sqlalchemy.orm import Mapped

# Initializing this at import time seems to be the only correct
# way to do this
db = flask_sqlalchemy.SQLAlchemy(model_class=Base)


@dataclass
class Bank(db.Model):  # type: ignore[name-defined]
    __tablename__ = "banks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    enabled_ratio: Mapped[float] = mapped_column(default=1.0)

    content: Mapped[t.List["BankContent"]] = relationship(
        back_populates="bank", cascade="all, delete"
    )

    def as_storage_iface_cls(self) -> BankConfig:
        return BankConfig(self.name, self.enabled_ratio)


@dataclass
class BankContent(db.Model):  # type: ignore[name-defined]
    __tablename__ = "bank_content"

    id: Mapped[int] = mapped_column(primary_key=True)
    bank_id: Mapped[int] = mapped_column(ForeignKey("bank.id"))
    bank: Mapped[Bank] = relationship(back_populates="content")

    disable_until_ts: Mapped[int] = mapped_column(default=BankContentConfig.ENABLED)
    original_content_uri: Mapped[t.Optional[str]]

    signals: Mapped[t.List["ContentSignal"]] = relationship(cascade="all, delete")

    def as_storage_iface_cls(self) -> BankContentConfig:
        return BankContentConfig(
            self.id,
            disable_until_ts=self.disable_until_ts,
            collab_metadata={},
            original_media_uri=None,
        )


@dataclass
class ContentSignal(db.Model):  # type: ignore[name-defined]
    id: Mapped[int] = mapped_column(primary_key=True)
    content_id: Mapped[int] = mapped_column(ForeignKey("bank_content.id"))
    signal_type: Mapped[str]
    signal_val: Mapped[str] = mapped_column(Text)
    id: Mapped[int] = db.Column(dbtypes.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = db.Column(dbtypes.String(255), nullable=False)
    enabled: Mapped[bool] = db.Column(dbtypes.Boolean, nullable=False)


@dataclass
class Hash(db.Model):  # type: ignore[name-defined]  # Should this be Signal?
    __tablename__ = "hashes"
    id = db.Column(dbtypes.Integer, primary_key=True, autoincrement=True)
    enabled = db.Column(dbtypes.Boolean, nullable=False)
    value = db.Column(dbtypes.LargeBinary, nullable=False)
    # We may need a pointer back to the 3rd party ID to do SEEN writebacks


@dataclass
class Exchange(db.Model):
    __tablename__ = "exchanges"
    id = db.Column(dbtypes.Integer, primary_key=True, autoincrement=True)
    name = db.Column(dbtypes.String(255), nullable=False, unique=True)
    # This might be better as an enum, but right now I don't know what 
    # the valid enum values would be, so leaving it as string
    type = db.Column(dbtypes.String(255), nullable=False)
    fetching_enabled = db.Column(dbtypes.Boolean, nullable=False, default=True)
    seen_enabled = db.Column(dbtypes.Boolean, nullable=False, default=True)
    report_true_positive = db.Column(dbtypes.Boolean, nullable=False, default=True)
    report_false_positive = db.Column(dbtypes.Boolean, nullable=False, default=True)
    additional_config = db.Column(dbtypes.JSON, nullable=False)
