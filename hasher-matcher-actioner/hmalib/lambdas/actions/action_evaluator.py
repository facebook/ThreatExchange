# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import boto3
import json
import os
import typing as t

from dataclasses import dataclass, field
from functools import lru_cache
from hmalib.common.logging import get_logger
from hmalib.common.classification_models import (
    BankedContentIDClassificationLabel,
    BankIDClassificationLabel,
    BankSourceClassificationLabel,
    ClassificationLabel,
    WritebackTypes,
    Label,
)
from hmalib.common.writebacker_models import ThreatExchangeSawThisTooWritebacker
from hmalib.common.config import HMAConfig
from hmalib.common.evaluator_models import (
    Action,
    ActionLabel,
    ActionRule,
)
from hmalib.common.message_models import (
    ActionMessage,
    BankedSignal,
    MatchMessage,
    WritebackMessage,
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
    writebacks_queue_url: str
    sqs_client: SQSClient

    @classmethod
    @lru_cache(maxsize=None)
    def get(cls):
        logger.info(
            "Initializing configs using table name %s", os.environ["CONFIG_TABLE_NAME"]
        )
        HMAConfig.initialize(os.environ["CONFIG_TABLE_NAME"])
        return cls(
            actions_queue_url=os.environ["ACTIONS_QUEUE_URL"],
            writebacks_queue_url=os.environ["WRITEBACKS_QUEUE_URL"],
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
        logger.info("sqs record body %s", sqs_record["body"])
        match_message = MatchMessage.from_aws_json(sqs_record_body["Message"])

        logger.info("Evaluating match_message: %s", match_message)

        action_rules = get_action_rules()

        logger.info("Evaluating against action_rules: %s", action_rules)

        action_label_to_action_rules = get_actions_to_take(match_message, action_rules)
        action_labels = list(action_label_to_action_rules.keys())
        for action_label in action_labels:
            action_message = (
                ActionMessage.from_match_message_action_label_and_action_rules(
                    match_message,
                    action_label,
                    action_label_to_action_rules[action_label],
                )
            )

            logger.info("Sending Action message: %s", action_message)
            config.sqs_client.send_message(
                QueueUrl=config.actions_queue_url,
                MessageBody=action_message.to_aws_json(),
            )

        for writeback_message in get_writeback_messages(match_message, action_labels):
            logger.info("Sending Writeback message: %s", writeback_message)
            config.sqs_client.send_message(
                QueueUrl=config.writebacks_queue_url,
                MessageBody=writeback_message.to_aws_json(),
            )

    return {"evaluation_completed": "true"}


def get_actions_to_take(
    match_message: MatchMessage, action_rules: t.List[ActionRule]
) -> t.Dict[ActionLabel, t.List[ActionRule]]:
    """
    Returns action labels for each action rule that applies to a match message.
    """
    action_label_to_action_rules: t.Dict[ActionLabel, t.List[ActionRule]] = dict()
    for banked_signal in match_message.matching_banked_signals:
        for action_rule in action_rules:
            if action_rule_applies_to_classifications(
                action_rule, banked_signal.classifications
            ):
                if action_rule.action_label in action_label_to_action_rules:
                    action_label_to_action_rules[action_rule.action_label].append(
                        action_rule
                    )
                else:
                    action_label_to_action_rules[action_rule.action_label] = [
                        action_rule
                    ]
    action_label_to_action_rules = remove_superseded_actions(
        action_label_to_action_rules
    )
    return action_label_to_action_rules


def get_action_rules() -> t.List[ActionRule]:
    """
    TODO Research caching rules for a short bit of time (1 min? 5 min?) use @lru_cache to implement
    Returns the ActionRule objects stored in the config repository. Each ActionRule
    will have the following attributes: MustHaveLabels, MustNotHaveLabels, ActionLabel.
    """
    return ActionRule.get_all()


def action_rule_applies_to_classifications(
    action_rule: ActionRule, classifications: t.Set[Label]
) -> bool:
    """
    Evaluate if the action rule applies to the classifications. Return True if the action rule's "must have"
    labels are all present and none of the "must not have" labels are present in the classifications, otherwise return False.
    """
    return action_rule.must_have_labels.issubset(
        classifications
    ) and action_rule.must_not_have_labels.isdisjoint(classifications)


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
    action_label_to_action_rules: t.Dict[ActionLabel, t.List[ActionRule]],
) -> t.Dict[ActionLabel, t.List[ActionRule]]:
    """
    TODO implement
    Evaluates a dictionary of action labels and the associated action rules generated for
    a match message against the actions. Action labels that are superseded by another will
    be removed.
    """
    return action_label_to_action_rules


def get_writeback_messages(
    match_message: MatchMessage,
    action_labels: t.List[ActionLabel],
) -> t.List[WritebackMessage]:
    """
    TODO implement
    Evaluates a collection of action_labels against some yet to be defined configuration
    (and possible business login) to produce
    """
    writeback_label = WritebackTypes.SawThisToo
    return [
        WritebackMessage.from_match_message_and_label(match_message, writeback_label)
    ]


if __name__ == "__main__":
    # For basic debugging
    HMAConfig.initialize(os.environ["CONFIG_TABLE_NAME"])
    action_rules = get_action_rules()
    match_message = MatchMessage(
        content_key="images/200200.jpg",
        content_hash="20f66f3a2e6eff06d895a8f421c045e1c76f0bf87652d72ce7249412d8d52acc",
        matching_banked_signals=[
            BankedSignal(
                banked_content_id="3534976909868947",
                bank_id="303636684709969",
                bank_source="te",
                classifications={
                    Label(key="BankIDClassification", value="303636684709969"),
                    Label(key="Classification", value="true_positive"),
                    Label(key="BankSourceClassification", value="te"),
                    Label(
                        key="BankedContentIDClassification", value="3534976909868947"
                    ),
                },
            )
        ],
    )
    action_label_to_action_rules = get_actions_to_take(match_message, action_rules)
    action_labels = list(action_label_to_action_rules.keys())
