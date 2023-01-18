# Copyright (c) Meta Platforms, Inc. and affiliates.

from dataclasses import dataclass, field
from hmalib.common.logging import get_logger

logger = get_logger(__name__)


@dataclass(unsafe_hash=True)
class Label:
    key: str
    value: str

    def __eq__(self, other) -> bool:
        # Concrete type doesnt matter for equality, only key, value
        # eg the following are equal:
        #   ClassificationLabel("Classification", "true_positive")
        #   Label("Classification", "true_positive")
        return (
            isinstance(other, Label)
            and self.key == other.key
            and self.value == other.value
        )


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
    # TODO name confusing. Should probably be SignalID...
    key: str = field(default="BankedContentIDClassification", init=False)


@dataclass(unsafe_hash=True)
class SubmittedContentClassificationLabel(ClassificationLabel):
    key: str = field(default="SubmittedContent", init=False)


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
    RemoveOpinion = WritebackType("RemoveOpinion")

    NoWriteback = WritebackType("NoWriteback")
