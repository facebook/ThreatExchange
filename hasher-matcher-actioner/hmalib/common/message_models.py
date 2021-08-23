# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import os
from urllib.parse import unquote_plus
import boto3
import typing as t
from dataclasses import dataclass, field

from hmalib.common.classification_models import (
    WritebackTypes,
)
from hmalib.common.messages.match import MatchMessage, BankedSignal
from hmalib.common.models.signal import PendingOpinionChange
from hmalib.common.configs.evaluator import ActionLabel, ActionRule
from hmalib.common.aws_dataclass import HasAWSSerialization
from hmalib.common.logging import get_logger

from mypy_boto3_sqs import SQSClient
from functools import lru_cache

logger = get_logger(__name__)


@dataclass
class ActionMessage(MatchMessage):
    """
    The action performer needs the match message plus which action to perform
    """

    action_label: ActionLabel = ActionLabel("UnspecifiedAction")
    action_rules: t.List[ActionRule] = field(default_factory=list)

    # from content
    additional_fields: t.List[str] = field(default_factory=list)

    @classmethod
    def from_match_message_action_label_action_rules_and_additional_fields(
        cls,
        match_message: MatchMessage,
        action_label: ActionLabel,
        action_rules: t.List[ActionRule],
        additional_fields=t.List[str],
    ) -> "ActionMessage":
        return cls(
            match_message.content_key,
            match_message.content_hash,
            match_message.matching_banked_signals,
            action_label,
            action_rules,
            additional_fields,
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
