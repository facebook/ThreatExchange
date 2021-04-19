# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json

from hmalib.common.logging import get_logger

logger = get_logger(__name__)


def lambda_handler(event, context):
    """
    This is the main entry point for reacting to ThreatExchange. The action evaluator
    sends a reaction message by way of the reactions queue and here's where they're
    popped off and dealt with.
    """
    for sqs_record in event["Records"]:
        # TODO research max # sqs records / lambda_handler invocation
        sqs_record_body = json.loads(sqs_record["body"])

        if sqs_record_body.get("Event") == "TestEvent":
            logger.info("Disregarding test: %s", sqs_record_body)
            continue

        logger.info("Reactin with sqs_record_body = %s", sqs_record_body)
        # TODO next PR will include implementation of the ReactionMessage class

    return {"reaction_completed": "true"}
