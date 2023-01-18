# Copyright (c) Meta Platforms, Inc. and affiliates.

import os
import boto3
import typing as t
from dataclasses import dataclass, field

from hmalib.common.classification_models import (
    WritebackTypes,
)
from hmalib.common.messages.match import MatchMessage, BankedSignal
from hmalib.common.models.signal import PendingThreatExchangeOpinionChange
from hmalib.common.aws_dataclass import HasAWSSerialization
from hmalib.common.logging import get_logger

from mypy_boto3_sqs import SQSClient
from functools import lru_cache

logger = get_logger(__name__)


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
        cls,
        banked_signal: BankedSignal,
        opinion_change: PendingThreatExchangeOpinionChange,
    ) -> "WritebackMessage":
        opinion_change_to_writeback_type = {
            PendingThreatExchangeOpinionChange.MARK_TRUE_POSITIVE: WritebackTypes.TruePositive,
            PendingThreatExchangeOpinionChange.MARK_FALSE_POSITIVE: WritebackTypes.FalsePositive,
            PendingThreatExchangeOpinionChange.REMOVE_OPINION: WritebackTypes.RemoveOpinion,
        }

        writeback_type = opinion_change_to_writeback_type.get(
            opinion_change, WritebackTypes.NoWriteback
        )

        return cls(
            [banked_signal],
            writeback_type,
        )

    def send_to_queue(self, sqs_client: SQSClient, queue_url: str) -> None:
        if self.writeback_type == WritebackTypes.NoWriteback:
            return

        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=self.to_aws_json(),
        )
