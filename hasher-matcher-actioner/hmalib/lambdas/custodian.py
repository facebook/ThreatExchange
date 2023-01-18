# Copyright (c) Meta Platforms, Inc. and affiliates.

import datetime
import os
import random
import string
from hmalib.common.logging import get_logger
from hmalib.common.timebucketizer import TimeBucketizer
from hmalib.common.models.pipeline import HashRecord

logger = get_logger(__name__)

os.environ["PATH"] = "/tmp/makethisdirectory/"

TYPE = ["hasher"]

BUCKET_WIDTH = datetime.timedelta(minutes=10)


def lambda_handler(event, context):
    """
    Squash the records of multiple timebucketizers into a single file
    """
    for value in TYPE:
        TimeBucketizer.squash_content(
            datetime.datetime.now(), value, os.environ["PATH"], BUCKET_WIDTH
        )
