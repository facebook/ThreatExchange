# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import hmalib.common.config as config
import json
import typing as t

from dataclasses import dataclass, field, fields
from hmalib.common.logging import get_logger
from requests import get, post, put, delete, Response

logger = get_logger(__name__)


@dataclass(unsafe_hash=True)
class Label:
    key: str
    value: str


@dataclass(unsafe_hash=True)
class ClassificationLabel(Label):
    key: str = field(default="Classification", init=False)


@dataclass(unsafe_hash=True)
class BankSourceClassificationLabel(ClassificationLabel):
    key: str = field(default="BankSourceClassification", init=False)


@dataclass(unsafe_hash=True)
class BankIDClassificationLabel(ClassificationLabel):
    key: str = field(default="BankIDClassification", init=False)


@dataclass(unsafe_hash=True)
class BankedContentIDClassificationLabel(ClassificationLabel):
    key: str = field(default="BankedContentIDClassification", init=False)


@dataclass(unsafe_hash=True)
class ActionLabel(Label):
    key: str = field(default="Action", init=False)


class WritebackTypes:
    @dataclass(unsafe_hash=True)
    class WritebackType(Label):
        key: str = field(default="Writeback", init=False)

    SawThisToo = WritebackType("SawThisToo")
    FalsePositive = WritebackType("FalsePositive")
    TruePositive = WritebackType("TruePositive")
    Ingested = WritebackType("Ingested")

    UnspecifiedWriteback = WritebackType("UnspecifiedWriteback")
