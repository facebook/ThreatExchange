# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json
import typing as t

from hmalib.common.logging import get_logger
from hmalib.models import MatchMessage, Label

logger = get_logger(__name__)


def lambda_handler(event, context):
    """
    This lambda is called when one or more matches are found. If a single hash matches
    multiple datasets, this will be called only once.

    Action labels are generated for each match message, then an action is performed
    corresponding to each action label.
    """
    for sqs_record in event[
        "Records"
    ]:  # confused about this... are we popping off more than one thing at a time from the "matches" queue?
        sns_notification = json.loads(sqs_record["body"])
        match_message: MatchMessage = MatchMessage.from_sns_message(
            sns_notification["Message"]
        )
        action_labels = get_action_labels(match_message)
        for action_label in action_labels:
            perform_action(match_message, action_label)

        # the more I write code here about reacting to ThreatExchange, the more I wish it was somewhere else entirely. Implementing
        # here forever ties up action-related code with ThreatExchange-specific code / functionality. I prefer putting
        # ThreatExchange-related specifics for reacting into another lambda that also subscribes to the matcher's notifications.
        if threat_exchange_reacting_is_enabled():
            threat_exchange_reaction_labels = get_threat_exchange_reaction_labels(
                action_labels
            )
            if threat_exchange_reaction_labels is t.List[Label]:
                for threat_exchange_reaction_label in threat_exchange_reaction_labels:
                    react_to_threat_exchange(
                        match_message, threat_exchange_reaction_label
                    )


def get_action_labels(match_message: MatchMessage) -> t.List[ActionLabel]:
    """
    TODO finish implementation
    Returns an ActionLabel for each ActionRule that applies to a MatchMessage.
    """
    action_rules = get_action_rules()
    action_labels = []  # use Set here
    for action_rule in action_rules:
        if action_rule.applies(match_message) and not action_labels.contains(
            action_rule.action_label
        ):
            action_labels.append(action_rule.action_label)
    action_labels = remove_superseded_actions(action_labels)  # maybe not needed for v0
    return action_labels


def get_action_rules() -> t.List[ActionRule]:
    """
    TODO implement
    Returns a collection of ActionRule objects. An ActionRule will have the following attributes:
    MustHaveLabels, MustNotHaveLabels, ActionLabel
    """
    return [
        ActionRule(
            ActionLabel("Action", "EnqueueForReview"),
            [Label("Collaboration", "12345")],
            [],
        )
    ]


def get_actions() -> t.List[Action]:
    """
    TODO implement
    Returns a collection of Action objects. An Action will have the following attributes:
    ActionLabel, Priority, SupersededByActionLabel
    """
    return [
        Action(
            ActionLabel("Action", "EnqueueForReview"),
            1,
            [ActionLabel("Action", "SomeMoreImortantAction")],
        )
    ]


def remove_superseded_actions(
    action_labels: t.List[ActionLabel],
) -> t.List[ActionLabel]:
    """
    TODO implement
    Evaluates a collection of ActionLabels against the configured Action objects, removing
    an ActionLabel when it's superseded by another.
    """
    return action_labels


def threat_exchange_reacting_is_enabled() -> bool:
    """
    TODO implement
    Looks up whether ThreatExchange reactions are enabled.
    """
    return True


def get_threat_exchange_reaction_labels(
    action_labels: t.List[ActionLabel],
) -> t.List[Label]:
    """
    TODO implement
    Evaluates a collection of action_labels against some yet to be defined configuration
    (and possible business login) to produce
    """
    return [Label("ThreatExchangeReaction", "SawThisToo")]


def perform_writeback_in_review(match_message: MatchMessage):
    # TODO implement
    logger.debug("wrote back IN_REVEIW")


def perform_enque_for_review(match_message: MatchMessage):
    # TODO implement
    logger.debug("enqued for review")


possible_actions = {
    "WRITEBACK_IN_REVIEW": perform_writeback_in_review,
    "ENQUE_FOR_REVIEW": perform_enque_for_review,
}


class ActionLabel(Label):
    def __init__(self, key: str, value: str):
        if key != "Action":
            raise Exception("ActionLabels must have a key Action")

        if value not in possible_actions.keys():
            raise Exception(f"'%s' is not a valid Action" % value)

        super(self.__class__, self).__init__(key, value)


class Action:
    action_label: ActionLabel
    priority: int
    superseded_by: t.List[ActionLabel]

    def __init__(
        self,
        action_label: ActionLabel,
        priority: int,
        superseded_by: t.List[ActionLabel],
    ):
        self.action_label = action_label
        self.priority = priority
        self.superseded_by = superseded_by


class ActionRule:
    action_label: ActionLabel
    must_have_labels: t.List[Label]
    must_not_have_labels: t.List[Label]

    def __init__(
        self,
        action_label: ActionLabel,
        must_have_labels: t.List[Label],
        must_not_have_labels: t.List[Label],
    ):
        self.action_label = action_label
        self.must_have_labels = must_have_labels
        self.must_not_have_labels = must_not_have_labels


def perform_action(match_message: MatchMessage, action_label: ActionLabel):
    for action, action_performer in possible_actions.items():
        if action is action_label.value:
            action_performer(match_message)


def react_to_threat_exchange(match_message: MatchMessage, reaction_label: Label):
    # TODO implement
    logger.debug("react to threat exchange")


# if __name__ == "__main__":
#    # For basic debugging
#    match_message = MatchMessage("key", "hash", [])
#    action_label = ActionLabel("Action", "ENQUE_FOR_REVIEW")

#    perform_action(match_message, action_label)
