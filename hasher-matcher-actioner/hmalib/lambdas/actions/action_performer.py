# Copyright (c) Meta Platforms, Inc. and affiliates.

import os
import boto3
import datetime
from functools import lru_cache
from mypy_boto3_dynamodb import DynamoDBServiceResource

from hmalib.common.messages.action import ActionMessage
from hmalib.common.configs.actioner import ActionPerformer
from hmalib.common.models.content import ActionEvent
from hmalib.common.logging import get_logger
from hmalib.common import config


logger = get_logger(__name__)
dynamodb: DynamoDBServiceResource = boto3.resource("dynamodb")

DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]


@lru_cache(maxsize=1)
def lambda_init_once():
    """
    Do some late initialization for required lambda components.

    Lambda initialization is weird - despite the existence of perfectly
    good constructions like __name__ == __main__, there don't appear
    to be easy ways to split your lambda-specific logic from your
    module logic except by splitting up the files and making your
    lambda entry as small as possible.

    TODO: Just refactor this file to separate the lambda and functional
          components
    """
    config_table = os.environ["CONFIG_TABLE_NAME"]
    config.HMAConfig.initialize(config_table)


def lambda_handler(event, context):
    """
    This is the main entry point for performing an action. The action evaluator puts
    an action message on the actions queue and here's where they're popped
    off and dealt with.
    """
    records_table = dynamodb.Table(DYNAMODB_TABLE)

    lambda_init_once()
    for sqs_record in event["Records"]:
        # TODO research max # sqs records / lambda_handler invocation
        action_message = ActionMessage.from_aws_json(sqs_record["body"])

        logger.info("Performing action: action_message = %s", action_message)

        if action_performer := ActionPerformer.get(action_message.action_label.value):
            action_performer.perform_action(action_message)
            ActionEvent(
                content_id=action_message.content_key,
                performed_at=datetime.datetime.now(),
                action_label=action_message.action_label.value,
                # v0 Hacks: the label rules model is super mutable we store basically the whole state
                # for each action performed. (~gross but until we have a unique id and version
                # it's what we've got).
                # Right now this just make json blob for action_performer and a list of
                # json blobs for action_rules that we can store and recover if needed.
                action_performer=action_performer.to_aws_json(),
                action_rules=[
                    rule.to_aws_json() for rule in action_message.action_rules
                ],
            ).write_to_table(records_table)
