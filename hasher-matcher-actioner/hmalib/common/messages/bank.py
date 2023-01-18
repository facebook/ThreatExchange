# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t
from dataclasses import dataclass

from threatexchange.content_type.content_base import ContentType
from threatexchange.signal_type.signal_base import SignalType

from hmalib.common.mappings import HMASignalTypeMapping


@dataclass
class BankSubmissionMessage:
    """
    Content has been submitted to a bank and now needs to be hashed. Once
    hashed, these will be added as BankMemberSignals.

    Resembles URLSubmissionMessage, actually is one with a few more fields to
    make BankMemberSignal objects.
    """

    content_type: t.Type[ContentType]

    # Must be a presigned url. Must be `url` so can be processed as other url messages.
    url: str

    bank_id: str
    bank_member_id: str

    event_type: str = "BankSubmissionMessage"

    def to_sqs_message(self) -> dict:
        return {
            "ContentType": self.content_type.get_name(),
            "URL": self.url,
            "BankId": self.bank_id,
            "BankMemberId": self.bank_member_id,
            "EventType": self.event_type,
        }

    @classmethod
    def from_sqs_message(
        cls, d: dict, signal_type_mapping: HMASignalTypeMapping
    ) -> "BankSubmissionMessage":
        return cls(
            content_type=signal_type_mapping.get_content_type_enforce(d["ContentType"]),
            url=d["URL"],
            bank_id=d["BankId"],
            bank_member_id=d["BankMemberId"],
            event_type=d["EventType"],
        )

    @classmethod
    def could_be(cls, d: dict) -> bool:
        return "EventType" in d and d["EventType"] == BankSubmissionMessage.event_type
