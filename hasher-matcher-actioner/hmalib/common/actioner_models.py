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


class LabelWithConstraints(Label):
    _KEY_CONSTRAINT = "KeyConstraint"

    def __init__(self, value: str):
        super(LabelWithConstraints, self).__init__(self._KEY_CONSTRAINT, value)


class ActionLabel(LabelWithConstraints):
    _KEY_CONSTRAINT = "Action"

    def __hash__(self) -> int:
        return self.value.__hash__()


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


@dataclass
class ActionPerformer:
    """
    A configuration of what action should be performed when a specific label
    is added to a match. Each label can lead to exactly one action being taken.

    To create a new type of ActionPerformer simply extend this class
    and add the necessary fields as attributes. All these attributes will be stored in AWS
    after update_aws_config is called. To retrieve from AWS the correct
    action performer for a label use the function ActionPerformerConfig.get_performer

    NOTE all attributes must be aws serializable. see config._py_to_aws_field for serialization logic
    """

    action_label: ActionLabel

    def perform_action(self, match_message: MatchMessage) -> None:
        raise NotImplementedError


@dataclass
class WebhookActionPerformer(ActionPerformer):
    url: TUrl

    def perform_action(self, match_message: MatchMessage) -> None:
        kwargs = {"data": match_message.to_aws_message()}
        self.call(**kwargs)

    def call(self, **kwargs) -> Response:
        raise NotImplementedError()


class WebhookPostActionPerformer(WebhookActionPerformer):
    def call(self, **kwargs) -> Response:
        data = kwargs.get("data")
        return post(self.url, data)


class WebhookGetActionPerformer(WebhookActionPerformer):
    def call(self, **kwargs) -> Response:
        return get(self.url)


class WebhookPutActionPerformer(WebhookActionPerformer):
    def call(self, **kwargs) -> Response:
        data = kwargs.get("data")
        return put(self.url, data)


class WebhookDeleteActionPerformer(WebhookActionPerformer):
    def call(self, **kwargs) -> Response:
        return delete(self.url)


def get_all_subclasses_rec(recursive: t.Set[t.Type]) -> t.Set[t.Type]:
    subclasses = {subclass for cls in recursive for subclass in cls.__subclasses__()}
    union = recursive.union(subclasses)
    if union != recursive:
        return get_all_subclasses_rec(union)
    return recursive


# TODO David said he wanted to refactor this
@dataclass
class ActionPerformerConfig(config.HMAConfig):
    """
    An adapter to use the HMAConfig Class to store differnet types of
    ActionPerformer configs. Since ActionPerformer configs are all unique by label but may
    be of different types, we store the name of the concrete type and the
    attributes of that type in AWS.

    DO NOT CALL config.HMAConfig FUNCTIONS DIRECTLY

    To load a config from a label use ActionPerformerConfig.get_performer

    To update an action performer ActionPerformerConfig.update_performer
    """

    concrete_type: str
    concrete_type_attrs: t.Dict[str, t.Any]

    @classmethod
    def get_performer(cls, action_label: ActionLabel) -> t.Optional["ActionPerformer"]:
        """
        Load from AWS the correct actioner config as the correct concrete class if it exists
        """
        name = action_label.value
        performer_config: t.Optional[ActionPerformerConfig] = cls.get(name)
        if performer_config:
            subclasses_classes = {
                cls.__name__: cls for cls in get_all_subclasses_rec({ActionPerformer})
            }
            return subclasses_classes[performer_config.concrete_type](
                action_label=action_label, **performer_config.concrete_type_attrs
            )
        return None

    @classmethod
    def update_performer(cls, action_performer: ActionPerformer) -> None:
        """
        Use this function to update the config in AWS instead of config.update_config directly
        """
        attrs = {
            field.name: getattr(action_performer, field.name)
            for field in fields(action_performer)
        }
        del attrs["action_label"]
        action_performer_config = ActionPerformerConfig(
            name=action_performer.action_label.value,
            concrete_type=action_performer.__class__.__name__,
            concrete_type_attrs=attrs,
        )
        config.update_config(action_performer_config)


if __name__ == "__main__":

    banked_signals = [
        BankedSignal("2862392437204724", "bank 4", "te"),
        BankedSignal("4194946153908639", "bank 4", "te"),
    ]
    match_message = MatchMessage("key", "hash", banked_signals)

    configs: t.List[ActionPerformer] = [
        WebhookDeleteActionPerformer(
            action_label=ActionLabel("DeleteWebhook"),
            url="https://webhook.site/ff7ebc37-514a-439e-9a03-46f86989e195",
        ),
        WebhookPutActionPerformer(
            action_label=ActionLabel("PutWebook"),
            url="https://webhook.site/ff7ebc37-514a-439e-9a03-46f86989e195",
        ),
    ]

    for action_config in configs:
        action_config.perform_action(match_message)
