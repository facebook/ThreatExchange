# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json
import os
import boto3
import typing as t
import datetime
from dataclasses import dataclass
from functools import lru_cache
from hmalib.common.message_models import BankedSignal, ActionMessage, MatchMessage
from hmalib.common.actioner_models import (
    ActionPerformer,
    WebhookPostActionPerformer,
)
from hmalib.models import PDQActionRecord
from hmalib.common.evaluator_models import ActionLabel
from hmalib.common.logging import get_logger
from mypy_boto3_dynamodb.service_resource import Table


from hmalib.common import config


logger = get_logger(__name__)


@dataclass
class ActionPerformerConfig:
    records_table: Table

    @classmethod
    @lru_cache(maxsize=None)
    def get(cls):
        config_table = os.environ["CONFIG_TABLE_NAME"]
        config.HMAConfig.initialize(config_table)

        DYNAMODB_RECORDS_TABLE = os.environ["DYNAMODB_RECORDS_TABLE"]
        dynamodb = boto3.resource("dynamodb")

        return cls(records_table=dynamodb.Table(DYNAMODB_RECORDS_TABLE))


def perform_label_action(
    match_message: MatchMessage, action_label: ActionLabel
) -> bool:
    if action_performer := ActionPerformer.get(action_label.value):
        action_performer.perform_action(match_message)
        return True
    return False


def lambda_handler(event, context):
    """
    This is the main entry point for performing an action. The action evaluator puts
    an action message on the actions queue and here's where they're popped
    off and dealt with.
    """
    config = ActionPerformerConfig.get()

    for sqs_record in event["Records"]:
        # TODO research max # sqs records / lambda_handler invocation
        action_message = ActionMessage.from_aws_json(sqs_record["body"])

        logger.info("Performing action: action_message = %s", action_message)

        perform_label_action(action_message, action_message.action_label)

        PDQActionRecord(
            content_id=action_message.content_key,
            content_hash=action_message.content_hash,
            updated_at=datetime.datetime.now(),
            action_label=action_message.action_label.value,
        ).write_to_table(config.records_table)

    return {"action_performed": "true"}


if __name__ == "__main__":
    os.environ["DYNAMODB_RECORDS_TABLE"] = "jeberl-HMADataStore"

    config = ActionPerformerConfig.get()

    banked_signals = [
        BankedSignal("2862392437204724", "bank 4", "te"),
        BankedSignal("4194946153908639", "bank 4", "te"),
    ]
    match_message = MatchMessage("key", "hash", banked_signals)

    action_message = ActionMessage(
        "key",
        "hash",
        matching_banked_signals=banked_signals,
        action_label=ActionLabel("EnqueForReview"),
    )
    event = {"Records": [{"body": action_message.to_aws_json()}]}
    lambda_handler(event, None)
