# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import hmalib.common.config as config
import json
import typing as t

from dataclasses import dataclass, field, fields
from hmalib.common.logging import get_logger
from hmalib.models import BankedSignal, MatchMessage
from requests import get, post, put, delete, Response

logger = get_logger(__name__)


@dataclass(unsafe_hash=True)
class Label:
    key: str
    value: str

    def __eq__(self, another_label: object) -> bool:
        if not isinstance(another_label, Label):
            return NotImplemented
        return self.key == another_label.key and self.value == another_label.value


@dataclass(unsafe_hash=True)
class ClassificationLabel(Label):
    key: str = field(default="Classification", init=False)


@dataclass(unsafe_hash=True)
class BankSourceClassificationLabel(Label):
    key: str = field(default="BankSourceClassification", init=False)


@dataclass(unsafe_hash=True)
class BankIDClassificationLabel(Label):
    key: str = field(default="BankIDClassification", init=False)


@dataclass(unsafe_hash=True)
class BankedContentIDClassificationLabel(Label):
    key: str = field(default="BankedContentIDClassification", init=False)


@dataclass(unsafe_hash=True)
class ActionLabel(Label):
    key: str = field(default="Action", init=False)


@dataclass(unsafe_hash=True)
class ThreatExchangeReactionLabel(Label):
    key: str = field(default="ThreatExchangeReaction", init=False)


@dataclass
class Action:
    action_label: ActionLabel
    priority: int
    superseded_by: t.List[ActionLabel]


@dataclass
class ActionRule(config.HMAConfig):
    """
    Action rules are config-backed objects that have a set of labels (both
    "must have" and "must not have") which, when evaluated against the
    classifications of a matching banked piece of content, lead to an action
    to take (specified by the rule's action label). By convention each action
    rule's name field is also the value field of the rule's action label.
    """

    action_label: ActionLabel
    must_have_labels: t.Set[Label]
    must_not_have_labels: t.Set[Label]


TUrl = t.Union[t.Text, bytes]


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
class ReactionMessage(MatchMessage):
    """
    The reactioner needs the match message plus which reaction to send back
    to the source of the signal (for now, ThreatExchange).
    """

    reaction_label: ThreatExchangeReactionLabel = field(
        default=ThreatExchangeReactionLabel("UnspecifiedThreatExchangeReaction")
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
class WebhookActionPerformer(ActionPerformer):
    """Superclass for webhooks"""

    url: str

    def perform_action(self, match_message: MatchMessage) -> None:
        self.call(data=json.dumps(match_message.to_aws()))

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
        WebhookDeleteActionPerformer(
            "DeleteWebhook", "https://webhook.site/ff7ebc37-514a-439e-9a03-46f86989e195"
        ),
        WebhookPutActionPerformer(
            "PutWebook", "https://webhook.site/ff7ebc37-514a-439e-9a03-46f86989e195"
        ),
    ]

    for action_config in configs:
        action_config.perform_action(match_message)
