# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json

from hmalib.common.logging import get_logger

logger = get_logger(__name__)

def lambda_handler(event, context):
    """
    This is the main entry point for reacting to ThreatExchange based on matching and
    actioning. The action evaluator puts <class-name-concept-phrase> on the reactions
    queue and here's where they're popped off and dealt with.
    """
    for sqs_record in event["Records"]:
        # TODO research max # sqs records / lambda_handler invocation
        sqs_record_body = json.loads(sqs_record["body"])
        logger.info(f"sqs_record_body = {sqs_record_body}")

    return {"action_performed": "true"}
