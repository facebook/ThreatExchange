# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
SQLAlchemy backed relational data.

We are trying to make all the persistent data accessed instead
through the storage interface. However, during development, that's
slower than just slinging sql on the tables, so you may see direct
references which are meant to be reaped at some future time.
"""

from dataclasses import dataclass

import flask_sqlalchemy

# Initializing this at import time seems to be the only correct
# way to do this
db = flask_sqlalchemy.SQLAlchemy()


@dataclass
class Bank(db.Model):  # type: ignore[name-defined]
    __tablename__ = "banks"
    id: int = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name: str = db.Column(db.String(255), nullable=False)
    enabled: bool = db.Column(db.Boolean, nullable=False)


@dataclass
class Hash(db.Model):  # type: ignore[name-defined]  # Should this be Signal?
    __tablename__ = "hashes"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    enabled = db.Column(db.Boolean, nullable=False)
    value = db.Column(db.LargeBinary, nullable=False)
    # We may need a pointer back to the 3rd party ID to do SEEN writebacks
