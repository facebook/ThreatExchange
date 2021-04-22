# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import hmalib.common.config as config
import json
import typing as t

from dataclasses import dataclass, fields
from hmalib.common.logging import get_logger
from hmalib.models import BankedSignal, MatchMessage
from requests import get, post, put, delete, Response

logger = get_logger(__name__)


@dataclass
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

    def __hash__(self) -> int:
        return self.value.__hash__()


class LabelWithConstraints(Label):
    _KEY_CONSTRAINT = "KeyConstraint"

    def __init__(self, value: str):
        super(LabelWithConstraints, self).__init__(self._KEY_CONSTRAINT, value)


class ClassificationLabel(LabelWithConstraints):
    _KEY_CONSTRAINT = "Classification"


class BankSourceClassificationLabel(LabelWithConstraints):
    _KEY_CONSTRAINT = "BankSource"


class BankIDClassificationLabel(LabelWithConstraints):
    _KEY_CONSTRAINT = "BankID"


class BankedContentIDClassificationLabel(LabelWithConstraints):
    _KEY_CONSTRAINT = "BankedContentID"


class ActionLabel(LabelWithConstraints):
    _KEY_CONSTRAINT = "Action"


class ThreatExchangeReactionLabel(LabelWithConstraints):
    _KEY_CONSTRAINT = "ThreatExchangeReaction"


@dataclass
class Action:
    action_label: ActionLabel
    priority: int
    superseded_by: t.List[ActionLabel]


@dataclass
class ActionRule:
    action_label: ActionLabel
    must_have_labels: t.List[Label]
    must_not_have_labels: t.List[Label]


TUrl = t.Union[t.Text, bytes]


@dataclass
class ActionMessage(MatchMessage):
    """
    The action performer needs the match message plus which action to perform
    TODO Create a reflection / introspection-based helper that implements
    to_ / from_aws_message code (and maybe from_match_message_and_label(), too)
    for ActionMessage and MatchMessage.
    """

    action_label: ActionLabel = ActionLabel("UnspecifiedAction")

    def to_aws_message(self) -> str:
        return json.dumps(
            {
                "ContentKey": self.content_key,
                "ContentHash": self.content_hash,
                "MatchingBankedSignals": [
                    x.to_dict() for x in self.matching_banked_signals
                ],
                "ActionLabelValue": self.action_label.value,
            }
        )

    @classmethod
    def from_aws_message(cls, message: str) -> "ActionMessage":
        parsed = json.loads(message)
        return cls(
            parsed["ContentKey"],
            parsed["ContentHash"],
            [BankedSignal.from_dict(d) for d in parsed["MatchingBankedSignals"]],
            ActionLabel(parsed["ActionLabelValue"]),
        )

    @classmethod
    def from_match_message_and_label(
        cls, match_message: MatchMessage, action_label: ActionLabel
    ) -> "ActionMessage":
        return cls(
            match_message.content_key,
            match_message.content_hash,
            match_message.matching_banked_signals,
            action_label,
        )


@dataclass
class ReactionMessage(MatchMessage):
    """
    The reactioner needs the match message plus which reaction to send back
    to the source of the signal (for now, ThreatExchange).
    """

    reaction_label: ThreatExchangeReactionLabel = ThreatExchangeReactionLabel(
        "UnspecifiedThreatExchangeReaction"
    )

    def to_aws_message(self) -> str:
        return json.dumps(
            {
                "ContentKey": self.content_key,
                "ContentHash": self.content_hash,
                "MatchingBankedSignals": [
                    x.to_dict() for x in self.matching_banked_signals
                ],
                "ReactionLabelValue": self.reaction_label.value,
            }
        )

    @classmethod
    def from_aws_message(cls, message: str) -> "ReactionMessage":
        parsed = json.loads(message)
        return cls(
            parsed["ContentKey"],
            parsed["ContentHash"],
            [BankedSignal.from_dict(d) for d in parsed["MatchingBankedSignals"]],
            ThreatExchangeReactionLabel(parsed["ReactionLabelValue"]),
        )

    @classmethod
    def from_match_message_and_label(
        cls,
        match_message: MatchMessage,
        threat_exchange_reaction_label: ThreatExchangeReactionLabel,
    ) -> "ReactionMessage":
        return cls(
            match_message.content_key,
            match_message.content_hash,
            match_message.matching_banked_signals,
            threat_exchange_reaction_label,
        )


class ActionPerformer(config.HMAConfigWithSubtypes):
    """
    An ActionPerfomer is the configuration + the code to perform an action.

    All actions share the same namespace (so that a post action and a
    "send to review" action can't both be called "IActionReview")

    ActionPerformer.get("action_name").perform_action(match_message)
    """

    @staticmethod
    def get_subtype_classes():
        return [
            WebhookPostActionPerformer,
            WebhookGetActionPerformer,
            WebhookPutActionPerformer,
            WebhookDeleteActionPerformer,
        ]

    # Implemented by subtypes
    def perform_action(self, match_message: MatchMessage) -> None:
        raise NotImplementedError


@dataclass
class WebhookActionPerformer(ActionPerformer.Subtype):  # type: ignore
    """Superclass for webhooks"""

    url: str

    def perform_action(self, match_message: MatchMessage) -> None:
        self.call(data=match_message.to_aws_message())

    def call(self, data: str) -> Response:
        raise NotImplementedError()


@dataclass
class WebhookPostActionPerformer(WebhookActionPerformer):
    """Hit an arbitrary endpoint with a POST"""

    def call(self, data: str) -> Response:
        return post(self.url, data)


@dataclass
class WebhookGetActionPerformer(WebhookActionPerformer):
    """Hit an arbitrary endpoint with a GET"""

    def call(self, _data: str) -> Response:
        return get(self.url)


@dataclass
class WebhookPutActionPerformer(WebhookActionPerformer):
    """Hit an arbitrary endpoint with a PUT"""

    def call(self, data: str) -> Response:
        return put(self.url, data)


@dataclass
class WebhookDeleteActionPerformer(WebhookActionPerformer):
    """Hit an arbitrary endpoint with a DELETE"""

    def call(self, _data: str) -> Response:
        return delete(self.url)


if __name__ == "__main__":

    banked_signals = [
        BankedSignal("2862392437204724", "bank 4", "te"),
        BankedSignal("4194946153908639", "bank 4", "te"),
    ]
    match_message = MatchMessage("key", "hash", banked_signals)

    configs: t.List[ActionPerformer] = [
        WebhookDeleteActionPerformer(  # type: ignore
            "DeleteWebhook", "https://webhook.site/ff7ebc37-514a-439e-9a03-46f86989e195"
        ),
        WebhookPutActionPerformer(  # type: ignore
            "PutWebook", "https://webhook.site/ff7ebc37-514a-439e-9a03-46f86989e195"
        ),
    ]

    for action_config in configs:
        action_config.perform_action(match_message)
