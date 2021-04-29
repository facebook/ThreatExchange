# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import typing as t

from dataclasses import dataclass, field
from hmalib.common.classification_models import Label
from hmalib.common.config import HMAConfig


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
class ActionRule(HMAConfig):
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
