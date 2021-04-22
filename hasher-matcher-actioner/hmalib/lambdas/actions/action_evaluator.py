# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import boto3
import json
import os
import typing as t

from dataclasses import dataclass, field
from functools import lru_cache
from hmalib.common.logging import get_logger
from hmalib.models import MatchMessage, BankedSignal
from hmalib.common.actioner_models import (
    Action,
    ActionLabel,
    ActionMessage,
    ActionRule,
    BankedContentIDClassificationLabel,
    BankIDClassificationLabel,
    BankSourceClassificationLabel,
    ClassificationLabel,
    Label,
    ReactionMessage,
    ThreatExchangeReactionLabel,
)
from hmalib.lambdas.actions.action_performer import perform_label_action
from mypy_boto3_sqs import SQSClient

logger = get_logger(__name__)


@dataclass
class ActionEvaluatorConfig:
    """
    Simple holder for getting typed environment variables
    """

    actions_queue_url: str
    reactions_queue_url: str
    sqs_client: SQSClient

    @classmethod
    @lru_cache(maxsize=None)
    def get(cls):
        return cls(
            actions_queue_url=os.environ["ACTIONS_QUEUE_URL"],
            reactions_queue_url=os.environ["REACTIONS_QUEUE_URL"],
            sqs_client=boto3.client("sqs"),
        )


def lambda_handler(event, context):
    """
    This lambda is called when one or more matches are found. If a single hash matches
    multiple datasets, this will be called only once.

    Action labels are generated for each match message, then an action is performed
    corresponding to each action label.
    """
    config = ActionEvaluatorConfig.get()

    for sqs_record in event["Records"]:
        # TODO research max # sqs records / lambda_handler invocation
        sqs_record_body = json.loads(sqs_record["body"])
        match_message = MatchMessage.from_aws_message(sqs_record_body["Message"])

        logger.info("Evaluating match_message: %s", match_message)

        action_rules = get_action_rules()

        logger.info("Evaluating against action_rules: %s", action_rules)

        action_labels = get_action_labels(match_message, action_rules)
        for action_label in action_labels:
            action_message = ActionMessage.from_match_message_and_label(
                match_message, action_label
            )
            config.sqs_client.send_message(
                QueueUrl=config.actions_queue_url,
                MessageBody=json.dumps(action_message.to_aws_message()),
            )

        if threat_exchange_reacting_is_enabled(match_message):
            threat_exchange_reaction_labels = get_threat_exchange_reaction_labels(
                match_message, action_labels
            )
            if threat_exchange_reaction_labels:
                for threat_exchange_reaction_label in threat_exchange_reaction_labels:
                    threat_exchange_reaction_message = (
                        ReactionMessage.from_match_message_and_label(
                            match_message, threat_exchange_reaction_label
                        )
                    )
                    config.sqs_client.send_message(
                        QueueUrl=config.reactions_queue_url,
                        MessageBody=json.dumps(
                            threat_exchange_reaction_message.to_aws_message()
                        ),
                    )

    return {"evaluation_completed": "true"}


def get_action_labels(
    match_message: MatchMessage, action_rules: t.List[ActionRule]
) -> t.Set[ActionLabel]:
    """
    Returns action labels for each action rule that applies to a match message.
    """
    classifications_by_match = get_classifications_by_match(match_message)
    action_labels: t.Set[ActionLabel] = set()
    for classifications in classifications_by_match:
        for action_rule in action_rules:
            if action_rule_applies_to_classifications(action_rule, classifications):
                action_labels.add(action_rule.action_label)
    action_labels = remove_superseded_actions(action_labels)
    return action_labels


def get_classifications_by_match(match_message: MatchMessage) -> t.List[t.Set[Label]]:
    """
    Creates a list of sets of classifications (as labels). Each set contains the labels that
    classify one matching banked piece of content.
    """
    classifications_by_match: t.List[t.Set[Label]] = list()

    for banked_signal in match_message.matching_banked_signals:
        classifications: t.Set[Label] = set()
        classifications.add(BankSourceClassificationLabel(banked_signal.bank_source))
        classifications.add(BankIDClassificationLabel(banked_signal.bank_id))
        classifications.add(
            BankedContentIDClassificationLabel(banked_signal.banked_content_id)
        )
        for classification in banked_signal.classifications:
            classifications.add(ClassificationLabel(classification))
        classifications_by_match.append(classifications)

    return classifications_by_match


def get_action_rules() -> t.List[ActionRule]:
    """
    TODO implement (get from config)
    Returns the ActionRule objects stored in the config repository. Each ActionRule
    will have the following attributes: MustHaveLabels, MustNotHaveLabels, ActionLabel.
    """
    return [
        ActionRule(
            ActionLabel("EnqueueForReview"),
            [
                BankIDClassificationLabel("303636684709969"),
                ClassificationLabel("true_positive"),
            ],
            [BankedContentIDClassificationLabel("3364504410306721")],
        )
    ]


def action_rule_applies_to_classifications(
    action_rule: ActionRule, classifications: t.Set[Label]
) -> bool:
    """
    Evaluate if the action rule applies to the classifications. Return True if the action rule's "must have"
    labels are all present and none of the "must not have" labels are present in the classifications, otherwise return False.
    """
    must_have_labels: t.Set[Label] = set(action_rule.must_have_labels)
    must_not_have_labels: t.Set[Label] = set(action_rule.must_not_have_labels)

    return must_have_labels.issubset(
        classifications
    ) and must_not_have_labels.isdisjoint(classifications)


def get_actions() -> t.List[Action]:
    """
    TODO implement
    Returns the Action objects stored in the config repository. Each Action will have
    the following attributes: ActionLabel, Priority, SupersededByActionLabel (Priority
    and SupersededByActionLabel are used by remove_superseded_actions).
    """
    return [
        Action(
            ActionLabel("EnqueueForReview"),
            1,
            [ActionLabel("A_MORE_IMPORTANT_ACTION")],
        )
    ]


def remove_superseded_actions(
    action_labels: t.Set[ActionLabel],
) -> t.Set[ActionLabel]:
    """
    TODO implement
    Evaluates a collection of ActionLabels generated for a match message against the actions.
    Action labels that are superseded by another will be removed.
    """
    return action_labels


def threat_exchange_reacting_is_enabled(match_message: MatchMessage) -> bool:
    """
    TODO implement
    Looks up from a config whether ThreatExchange reacting is enabled. Initially this will be a global
    config, and this method will return True if reacting is enabled, False otherwise. At some point the
    config for reacting to ThreatExchange may be on a per collaboration basis. In that case, the config
    will be referenced for each collaboration involved (implied by the match message). If reacting
    is enabled for a given collaboration, a label will be added to the match message
    (e.g. "ThreatExchangeReactingEnabled:<collaboration-id>").
    """
    return True


def get_threat_exchange_reaction_labels(
    match_message: MatchMessage,
    action_labels: t.List[ActionLabel],
) -> t.List[Label]:
    """
    TODO implement
    Evaluates a collection of action_labels against some yet to be defined configuration
    (and possible business login) to produce
    """
    return [ThreatExchangeReactionLabel("SAW_THIS_TOO")]


if __name__ == "__main__":
    # For basic debugging
    banked_signal = BankedSignal(
        "4169895076385542", "303636684709969", "te", ["true_positive", "Bar", "Xyz"]
    )
    match_message = MatchMessage("key", "hash", [banked_signal])

    print(
        f"get_action_labels({match_message}, {get_action_rules()}):\n\t{get_action_labels(match_message, get_action_rules())}\n\n"
    )

    banked_signal_2 = BankedSignal(
        "3364504410306721",
        "303636684709969",
        "te",
        ["true_positive", "Foo", "Bar", "Xyz"],
    )
    match_message_2 = MatchMessage("key", "hash", [banked_signal_2])

    print(
        f"get_action_labels({match_message_2}, {get_action_rules()}):\n\t{get_action_labels(match_message_2, get_action_rules())}\n\n"
    )
