# Copyright (c) Meta Platforms, Inc. and affiliates.

from urllib.parse import unquote_plus
import typing as t
from dataclasses import dataclass, field

from hmalib.common.classification_models import (
    BankedContentIDClassificationLabel,
    BankIDClassificationLabel,
    BankSourceClassificationLabel,
    ClassificationLabel,
    Label,
)
from hmalib.common.aws_dataclass import HasAWSSerialization
from hmalib.common.logging import get_logger


logger = get_logger(__name__)


@dataclass
class BankedSignal:
    """
    BankedSignal fields:
    - `banked_content_id`: Inside the bank, the unique way to refer to what
      was matched against
    - `bank_id`: The unique way to refer to the bank banked_content_id came from
    - `bank_source`: This is forward looking: this might be 'te' or 'local';
      indicates source of or relationship between one or more banks
    - `classifications`: a set of labels that provide context about the banked
       signal
    """

    banked_content_id: str
    bank_id: str
    bank_source: str
    classifications: t.Set[Label] = field(default_factory=set)

    def __post_init__(self):
        self.add_bank_classifications()

    def add_bank_classifications(self):
        if len(self.classifications) != 0:
            return

        self.classifications.add(BankSourceClassificationLabel(self.bank_source))
        self.classifications.add(BankIDClassificationLabel(self.bank_id))
        self.classifications.add(
            BankedContentIDClassificationLabel(self.banked_content_id)
        )

    def add_classification(self, classification: str):
        if len(self.classifications) == 0:
            self.add_bank_classifications()
        self.classifications.add(ClassificationLabel(classification))


@dataclass
class MatchMessage(HasAWSSerialization):
    """
    Captures a set of matches that will need to be processed. We create one
    match message for a single content key. It is possible that a single content
    hash matches multiple datasets. When it does, the entire set of matches are
    forwarded together so that any appropriate action can be taken.

    - `content_key`: A way for partners to refer uniquely to content on their
      site
    - `content_hash`: The hash generated for the content_key
    """

    content_key: str
    content_hash: str
    matching_banked_signals: t.List[BankedSignal] = field(default_factory=list)
