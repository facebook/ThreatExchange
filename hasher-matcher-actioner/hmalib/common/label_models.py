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

    def to_dynamodb_dict(self) -> dict:
        return {"K": self.key, "V": self.value}

    @classmethod
    def from_dynamodb_dict(cls, d: dict):
        return cls(d["K"], d["V"])

    def __eq__(self, another_label: object) -> bool:
        if not isinstance(another_label, Label):
            return NotImplemented
        return self.key == another_label.key and self.value == another_label.value


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


@dataclass(unsafe_hash=True)
class ReactionLabel(Label):
    key: str = field(default="Reaction", init=False)

    def __eq__(self, other) -> bool:
        return self.value == other.value


@dataclass(unsafe_hash=True)
class SawThisTooReactionLabel(ReactionLabel):
    value: str = field(default="SawThisToo", init=False)


@dataclass(unsafe_hash=True)
class FalsePositiveReactionLabel(ReactionLabel):
    value: str = field(default="FalsePositive", init=False)


@dataclass(unsafe_hash=True)
class TruePositiveReactionLabel(ReactionLabel):
    value: str = field(default="TruePositive", init=False)


@dataclass(unsafe_hash=True)
class InReviewReactionLabel(ReactionLabel):
    value: str = field(default="InReview", init=False)


@dataclass(unsafe_hash=True)
class IngestedReactionLabel(ReactionLabel):
    value: str = field(default="Ingested", init=False)