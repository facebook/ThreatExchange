# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json

from hmalib.common import get_logger
from hmalib.models import MatchMessage

logger = get_logger(__name__)


def lambda_handler(event, context):
    """
    The output SNS topics from matchers have SQS instances subscribed to them.
    This indirection allows for fanout. Multiple SQS queues can be tagged to the
    same SNS topic and SNS will guarantee delivery to the queues.

    Architecture aside, here's what you need to know. The actions layer will be
    listening on an SQS queue. For every record,
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
