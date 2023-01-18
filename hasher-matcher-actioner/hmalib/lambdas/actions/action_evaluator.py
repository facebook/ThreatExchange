# Copyright (c) Meta Platforms, Inc. and affiliates.

import boto3
import json
import os
import typing as t
from dataclasses import dataclass
from functools import lru_cache

from threatexchange.content_type.photo import PhotoContent

from hmalib.common.logging import get_logger
from hmalib.common.classification_models import (
    BankIDClassificationLabel,
    BankSourceClassificationLabel,
    BankedContentIDClassificationLabel,
    ClassificationLabel,
    SubmittedContentClassificationLabel,
    WritebackTypes,
    Label,
)
from hmalib.common.config import HMAConfig
from hmalib.common.configs.evaluator import (
    ActionLabel,
    ActionRule,
)
from hmalib.common.messages.action import ActionMessage
from hmalib.common.messages.match import BankedSignal, MatchMessage

from hmalib.common.messages.writeback import WritebackMessage
from hmalib.common.models.content import ContentObject
from mypy_boto3_sqs import SQSClient
from mypy_boto3_dynamodb.service_resource import Table, DynamoDBServiceResource


logger = get_logger(__name__)


@dataclass
class ActionEvaluatorConfig:
    """
    Simple holder for getting typed environment variables
    """

    actions_queue_url: str
    sqs_client: SQSClient
    dynamo_db_table: Table
    writeback_queue_url: str

    @classmethod
    @lru_cache(maxsize=None)
    def get(cls):
        logger.info(
            "Initializing configs using table name %s", os.environ["CONFIG_TABLE_NAME"]
        )
        logger.info(
            "Initializing dynamo table using table name %s",
            os.environ["DYNAMODB_TABLE"],
        )
        HMAConfig.initialize(os.environ["CONFIG_TABLE_NAME"])

        dynamo_db_table_name = os.environ["DYNAMODB_TABLE"]
        dynamodb: DynamoDBServiceResource = boto3.resource("dynamodb")

        writeback_queue_url = os.environ["WRITEBACKS_QUEUE_URL"]

        return cls(
            actions_queue_url=os.environ["ACTIONS_QUEUE_URL"],
            sqs_client=boto3.client("sqs"),
            dynamo_db_table=dynamodb.Table(dynamo_db_table_name),
            writeback_queue_url=writeback_queue_url,
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
        match_message = MatchMessage.from_aws_json(sqs_record_body["Message"])

        logger.info("Evaluating match_message: %s", match_message)

        action_rules = get_action_rules()

        logger.info("Evaluating against action_rules: %s", action_rules)

        submitted_content = ContentObject.get_from_content_id(
            config.dynamo_db_table, match_message.content_key
        )

        action_label_to_action_rules = get_actions_to_take(
            match_message,
            action_rules,
            submitted_content.additional_fields,
        )
        action_labels = list(action_label_to_action_rules.keys())
        for action_label in action_labels:
            action_message = ActionMessage.from_match_message_action_label_action_rules_and_additional_fields(
                match_message,
                action_label,
                action_label_to_action_rules[action_label],
                list(submitted_content.additional_fields),
            )

            logger.info("Sending Action message: %s", action_message)
            config.sqs_client.send_message(
                QueueUrl=config.actions_queue_url,
                MessageBody=action_message.to_aws_json(),
            )

        writeback_message = WritebackMessage.from_match_message_and_type(
            match_message, WritebackTypes.SawThisToo
        )
        writeback_message.send_to_queue(config.sqs_client, config.writeback_queue_url)

    return {"evaluation_completed": "true"}


def get_actions_to_take(
    match_message: MatchMessage,
    action_rules: t.List[ActionRule],
    additional_fields_on_content: t.Set[str],
) -> t.Dict[ActionLabel, t.List[ActionRule]]:
    """
    Returns action labels for each action rule that applies to a match message.
    """
    action_label_to_action_rules: t.Dict[ActionLabel, t.List[ActionRule]] = dict()

    content_classifications = {
        SubmittedContentClassificationLabel(field)
        for field in additional_fields_on_content
    }

    logger.info(
        "Adding SubmittedContentClassificationLabel(s): %s", content_classifications
    )

    for banked_signal in match_message.matching_banked_signals:
        for action_rule in action_rules:
            if action_rule_applies_to_classifications(
                action_rule,
                banked_signal.classifications.union(content_classifications),
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


if __name__ == "__main__":
    # For basic debugging
    HMAConfig.initialize(os.environ["CONFIG_TABLE_NAME"])
    action_rules = get_action_rules()
    match_message = MatchMessage(
        content_key="m2",
        content_hash="361da9e6cf1b72f5cea0344e5bb6e70939f4c70328ace762529cac704297354a",
        matching_banked_signals=[
            BankedSignal(
                banked_content_id="3070359009741438",
                bank_id="258601789084078",
                bank_source="te",
                classifications={
                    BankedContentIDClassificationLabel(value="258601789084078"),
                    ClassificationLabel(value="true_positive"),
                    BankSourceClassificationLabel(value="te"),
                    BankIDClassificationLabel(value="3534976909868947"),
                },
            )
        ],
    )

    event = {
        "Records": [{"body": json.dumps({"Message": match_message.to_aws_json()})}]
    }
    lambda_handler(event, None)
