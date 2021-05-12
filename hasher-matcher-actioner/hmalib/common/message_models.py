# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import os
import boto3
import typing as t
from dataclasses import dataclass, field
from hmalib.common.classification_models import (
    BankedContentIDClassificationLabel,
    BankIDClassificationLabel,
    BankSourceClassificationLabel,
    ClassificationLabel,
    Label,
    WritebackTypes,
    PendingOpinionChange,
)
from hmalib.common.evaluator_models import ActionLabel, ActionRule
from hmalib.common.aws_dataclass import HasAWSSerialization
from hmalib.common.config import HMAConfig
from mypy_boto3_sqs import SQSClient
from functools import lru_cache


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

    def add_bank_classifications(self):
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


@dataclass
class ActionMessage(MatchMessage):
    """
    The action performer needs the match message plus which action to perform
    """

    action_label: ActionLabel = ActionLabel("UnspecifiedAction")
    action_rules: t.List[ActionRule] = field(default_factory=list)

    @classmethod
    def from_match_message_action_label_and_action_rules(
        cls,
        match_message: MatchMessage,
        action_label: ActionLabel,
        action_rules: t.List[ActionRule],
    ) -> "ActionMessage":
        return cls(
            match_message.content_key,
            match_message.content_hash,
            match_message.matching_banked_signals,
            action_label,
            action_rules,
        )


@dataclass
class WritebackMessageConfig:
    """
    Simple holder for getting typed environment variables
    """

    writebacks_queue_url: str
    sqs_client: SQSClient

    @classmethod
    @lru_cache(maxsize=None)
    def get(cls):
        return cls(
            writebacks_queue_url=os.environ["WRITEBACKS_QUEUE_URL"],
            sqs_client=boto3.client("sqs"),
        )


@dataclass
class WritebackMessage(HasAWSSerialization):
    """
    Writebacks happen on a collection of BankedSignals. To perform a write back,
    instantiate an instacne of this class and run the send_to_queue method

    The Writebacker needs the match message plus which writeback type to perfrom
    on the source of the signal (for now, ThreatExchange).
    """

    banked_signals: t.List[BankedSignal]

    writeback_type: WritebackTypes.WritebackType = field(
        default=WritebackTypes.NoWriteback
    )

    @classmethod
    def from_match_message_and_type(
        cls,
        match_message: MatchMessage,
        writeback_type: WritebackTypes.WritebackType,
    ) -> "WritebackMessage":
        return cls(
            match_message.matching_banked_signals,
            writeback_type,
        )

    @classmethod
    def from_banked_signal_and_opinion_change(
        cls, banked_signal: BankedSignal, opinion_change: PendingOpinionChange
    ) -> "WritebackMessage":
        opinion_change_to_writeback_type = {
            PendingOpinionChange.MARK_TRUE_POSITIVE: WritebackTypes.TruePositive,
            PendingOpinionChange.MARK_FALSE_POSITIVE: WritebackTypes.FalsePositive,
            PendingOpinionChange.REMOVE_OPINION: WritebackTypes.RemoveOpinion,
        }

        writeback_type = opinion_change_to_writeback_type.get(
            opinion_change, WritebackTypes.NoWriteback
        )

        return cls(
            [banked_signal],
            writeback_type,
        )

    def send_to_queue(self) -> None:
        if self.writeback_type == WritebackTypes.NoWriteback:
            return

        config = WritebackMessageConfig.get()
        config.sqs_client.send_message(
            QueueUrl=config.writebacks_queue_url,
            MessageBody=self.to_aws_json(),
        )
