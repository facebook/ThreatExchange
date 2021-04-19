# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json
import typing as t
from hmalib.common.actioner_models import (
    ActionLabel,
    ActionPerformerConfig,
)

from dataclasses import dataclass, field
from hmalib.common.logging import get_logger
from hmalib.models import MatchMessage, Label, BankedSignal
from hmalib.common import config


def perform_label_action(match_message: MatchMessage, action_label: ActionLabel) -> int:
    action_performer = ActionPerformerConfig.get_performer(action_label)
    if action_performer:
        action_performer.perform_action(match_message)
        return 1
    return 0


def lambda_handler(event, context):
    """
    This is the main entry point for performing an action. The action evaluator puts
    an action message on the actions queue and here's where they're popped
    off and dealt with.
    """
    for sqs_record in event["Records"]:
        # TODO research max # sqs records / lambda_handler invocation
        sqs_record_body = json.loads(sqs_record["body"])

        if sqs_record_body.get("Event") == "TestEvent":
            logger.info("Disregarding test: %s", sqs_record_body)
            continue

        logger.info("Performing action: sqs_record_body = %s", sqs_record_body)

        # TODO instantiate an instance of ActionMessage here, then call perform_action()

    return {"action_performed": "true"}


if __name__ == "__main__":
    pass
