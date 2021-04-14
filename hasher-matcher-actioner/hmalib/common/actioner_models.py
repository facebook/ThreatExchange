# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

from dataclasses import dataclass
import typing as t

from hmalib.models import Label


class LabelWithConstraints(Label):
    _KEY_CONSTRAINT = "KeyConstraint"

    def __init__(self, value: str):
        super(LabelWithConstraints, self).__init__(self._KEY_CONSTRAINT, value)


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
