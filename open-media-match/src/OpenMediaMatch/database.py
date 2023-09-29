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


class ContentSignal(db.Model):  # type: ignore[name-defined]
    id: Mapped[int] = mapped_column(primary_key=True)
    content_id: Mapped[int] = mapped_column(ForeignKey("bank_content.id"))
    signal_type: Mapped[str]
    signal_val: Mapped[str] = mapped_column(Text)
