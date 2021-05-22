# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json
import os
import typing as t
from collections import defaultdict
import boto3

from hmalib.common.count_models import MatchByPrivacyGroupCounter
from hmalib.common.message_models import MatchMessage
from hmalib.common.logging import get_logger

DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]

logger = get_logger(__name__)
dynamodb = boto3.resource("dynamodb")


def lambda_handler(event, context):
    """
    Listens to events on a queue attached to the match SNS topic and increments
    various counters.

    Presently supported:
    ---
    1. split of hash and matches by privacy group
    """
    records_table = dynamodb.Table(DYNAMODB_TABLE)
    counters = defaultdict(lambda: 0)

    for sqs_record in event["Records"]:
        sqs_record_body = json.loads(sqs_record["body"])
        match_message = MatchMessage.from_aws_json(sqs_record_body["Message"])

        for signal in match_message.matching_banked_signals:
            privacy_group_id = signal.bank_id
            counters[privacy_group_id] += 1

    logger.debug("Flushing %s", counters)
    # Flush counters to dynamodb
    MatchByPrivacyGroupCounter.increment_counts(records_table, counters)
