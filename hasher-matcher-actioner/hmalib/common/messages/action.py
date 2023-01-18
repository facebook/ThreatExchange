# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t
from dataclasses import dataclass, field

from hmalib.common.messages.match import MatchMessage
from hmalib.common.configs.evaluator import ActionLabel, ActionRule
from hmalib.common.logging import get_logger


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
