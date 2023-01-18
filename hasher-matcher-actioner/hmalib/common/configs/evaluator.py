# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t

from dataclasses import dataclass, field
from hmalib.common.classification_models import Label, ActionLabel
from hmalib.common.config import HMAConfig
from hmalib.common.aws_dataclass import HasAWSSerialization


@dataclass
class Action:
    action_label: ActionLabel
    priority: int
    superseded_by: t.List[ActionLabel]


# This class should be kept in sync with TypeScript type BackendActionRule in API.tsx
@dataclass
class ActionRule(HMAConfig, HasAWSSerialization):
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
