# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json
import typing as t

from dataclasses import dataclass, field
from hmalib.common.logging import get_logger
from hmalib.common.actioner_models import (
    ActionLabel,
    ActionPerformer,
    WebhookActionPerformer,
    Post,
    Put,
)
from hmalib.models import MatchMessage, Label

logger = get_logger(__name__)


def perform_writeback_in_review(match_message: MatchMessage):
    # TODO implement
    logger.debug("wrote back IN_REVEIW")


def perform_enque_for_review(match_message: MatchMessage):
    # TODO implement
    logger.debug("enqued for review")


def perform_action(match_message: MatchMessage, action_label: ActionLabel) -> int:
    action_performer = get_action_perfromers_config().get(action_label)
    if action_performer:
        action_performer.perform_action(match_message)
        return 1
    return 0


def get_action_perfromers_config() -> t.Dict[ActionLabel, ActionPerformer]:
    # TODO Should Read From s3 Configs table and determine which performer dynamically
    return {
        ActionLabel("SendDemotePostWebhook"): WebhookActionPerformer(
            Post, "https://webhook.site/ff7ebc37-514a-439e-9a03-46f86989e195"
        ),
        ActionLabel("SendDeletePutWebhook"): WebhookActionPerformer(
            Put, "https://webhook.site/ff7ebc37-514a-439e-9a03-45635463"
        ),
    }


def react_to_threat_exchange(match_message: MatchMessage, reaction_label: Label):
    # TODO implement
    logger.debug("react to threat exchange")


def lambda_handler(event, context):
    """
    TODO: Currently action evaluator calls perform_action directly. We will eventually
    want to put an SQS queue in the middle which will call this function
    """
    return {"version": "1"}


if __name__ == "__main__":
    # For basic debugging
    match_message = MatchMessage("key", "hash", [])
    action_label = ActionLabel("SendDemotePostWebhook")

    perform_action(match_message, action_label)
