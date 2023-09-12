# Copyright (c) Meta Platforms, Inc. and affiliates.

from OpenMediaMatch import database as db


class Bank(db.Model):  # type: ignore[name-defined]  # mypy not smart enough
    __tablename__ = "banks"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    enabled = db.Column(db.Boolean, nullable=False)


class Hash(db.Model):  # type: ignore[name-defined]  # mypy not smart enough
    __tablename__ = "hashes"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    enabled = db.Column(db.Boolean, nullable=False)
    value = db.Column(db.LargeBinary, nullable=False)
