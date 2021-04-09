# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json

from hmalib.common.logging import get_logger
from hmalib.models import MatchMessage, Label

logger = get_logger(__name__)


def lambda_handler(event, context):
    """
    This lambda is called once per match per dataset. If a single hash matches
    multiple datasets, this will be called multiple times.

    Eventually, this will be just an action labeller. It will label a match
    record with the action it recommends. A separate system will be stood up
    that aggregates labels and 'decides' which action would be taken.

    For now, this method will,
    - it will construct the MatchMessage object and identify the actions it
      needs to invoke.
    - for now, rather than fanning out to individual specific lambdas, it will
      call all specific functions serially!
    """
    for sqs_record in event["Records"]:
        sns_notification = json.loads(sqs_record["body"])
        match_message: MatchMessage = MatchMessage.from_sns_message(
            sns_notification["Message"]
        )


def perform_writeback_in_review(match_message: MatchMessage):
    # TODO implement
    logger.debug("wrote back IN_REVEIW")


def perform_enque_for_review(match_message: MatchMessage):
    # TODO implement
    logger.debug("enqued for review")


possible_actions = {
    "WRITEBACK_IN_REVIEW": perform_writeback_in_review,
    "ENQUE_FOR_REVIEW": perform_enque_for_review,
}


class ActionLabel(Label):
    def __init__(self, key: str, value: str):
        if key != "Action":
            raise Exception("ActionLabels must have a key Action")

        if value not in possible_actions.keys():
            raise Exception(f"'%s' is not a valid Action" % value)

        super(self.__class__, self).__init__(key, value)


def perform_action(match_message: MatchMessage, action_label: ActionLabel):
    for action, action_performer in possible_actions.items():
        if action is action_label.value:
            action_performer(match_message)


if __name__ == "__main__":
    # For basic debugging
    match_message = MatchMessage("key", "hash", [])
    action_label = ActionLabel("Action", "ENQUE_FOR_REVIEW")

    perform_action(match_message, action_label)
