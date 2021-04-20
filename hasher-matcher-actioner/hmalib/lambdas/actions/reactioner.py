# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json

from hmalib.common.logging import get_logger
from hmalib.common.actioner_models import ReactionMessage

logger = get_logger(__name__)


def lambda_handler(event, context):
    """
    This is the main entry point for reacting to ThreatExchange. The action evaluator
    sends a reaction message by way of the reactions queue and here's where they're
    popped off and dealt with.
    """
    for sqs_record in event["Records"]:
        # TODO research max # sqs records / lambda_handler invocation
        reaction_message = ReactionMessage.from_aws_message(
            json.loads(sqs_record["body"])
        )

        logger.info("Reacting: reaction_message = %s", reaction_message)

    return {"reaction_completed": "true"}


if __name__ == "__main__":
    pass
