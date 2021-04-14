# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json
import typing as t

from dataclasses import dataclass, field
from hmalib.common.logging import get_logger
from hmalib.common.actioner_models import ActionLabel
from hmalib.models import MatchMessage, Label

logger = get_logger(__name__)


def perform_writeback_in_review(match_message: MatchMessage):
    # TODO implement
    logger.debug("wrote back IN_REVEIW")


def perform_enque_for_review(match_message: MatchMessage):
    # TODO implement
    logger.debug("enqued for review")


def perform_action(match_message: MatchMessage, action_label: ActionLabel):
    # TODO implement
    logger.debug("perform action")


def react_to_threat_exchange(match_message: MatchMessage, reaction_label: Label):
    # TODO implement
    logger.debug("react to threat exchange")


def lambda_handler(event, context):
    """
    TODO
    """
    pass


if __name__ == "__main__":
    # For basic debugging
    match_message = MatchMessage("key", "hash", [])
    action_label = ActionLabel("ENQUE_FOR_REVIEW")

    perform_action(match_message, action_label)
