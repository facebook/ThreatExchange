# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json
import typing as t
from hmalib.common.actioner_models import (
    ActionLabel,
    ActionPerformerConfig,
    ActionPerformer,
)

from dataclasses import dataclass, field
from hmalib.common.logging import get_logger
from hmalib.models import MatchMessage, Label
from hmalib.common import config

logger = get_logger(__name__)


def perform_writeback_in_review(match_message: MatchMessage):
    # TODO implement
    logger.debug("wrote back IN_REVEIW")


def perform_enque_for_review(match_message: MatchMessage):
    # TODO implement
    logger.debug("enqued for review")


def perform_label_action(match_message: MatchMessage, action_label: ActionLabel) -> int:
    action_performer = ActionPerformerConfig.get_performer(action_label)
    if action_performer:
        action_performer.perform_action(match_message)
        return 1
    return 0


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

    perform_label_action(match_message, action_label)
