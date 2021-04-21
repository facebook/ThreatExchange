# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json
from hmalib.common.actioner_models import (
    ActionLabel,
    ActionMessage,
    ActionPerformer,
)

from hmalib.common.logging import get_logger
from hmalib.models import MatchMessage


logger = get_logger(__name__)


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
    for sqs_record in event["Records"]:
        # TODO research max # sqs records / lambda_handler invocation
        action_message = ActionMessage.from_aws_message(json.loads(sqs_record["body"]))

        logger.info("Performing action: action_message = %s", action_message)

        perform_label_action(action_message, action_message.action_label)

    return {"action_performed": "true"}
