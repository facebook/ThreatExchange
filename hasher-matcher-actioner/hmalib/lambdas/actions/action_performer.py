# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json

from hmalib.common import get_logger
from hmalib.models import MatchMessage

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
