# Copyright (c) Meta Platforms, Inc. and affiliates.

from dataclasses import dataclass
from OpenMediaMatch import db


@dataclass
class Bank(db.Model):
    __tablename__ = "banks"
    id: int = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name: str = db.Column(db.String(255), nullable=False)
    enabled: bool = db.Column(db.Boolean, nullable=False)


@dataclass
class Hash(db.Model):
    __tablename__ = "hashes"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    enabled = db.Column(db.Boolean, nullable=False)
    value = db.Column(db.LargeBinary, nullable=False)
