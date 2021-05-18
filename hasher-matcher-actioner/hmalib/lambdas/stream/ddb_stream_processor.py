# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

from hmalib.common.count_models import MatchByPrivacyGroupCounter
import os
import typing as t
from collections import defaultdict
import boto3

from hmalib.common.logging import get_logger

DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]

logger = get_logger(__name__)
dynamodb = boto3.resource("dynamodb")


def _is_hash_record(item_image: t.Dict) -> bool:
    """
    Returns True if the new image looks like a hash record. At present, supports
    PDQ shapes only.
    """
    return (
        "ContentHash" in item_image
        and "HashType" in item_image
        and item_image["HashType"] == {"S": "pdq"}
        and "Quality" in item_image
        and "SignalSource" not in item_image
    )


def _is_match_record(item_image: t.Dict) -> bool:
    """
    Returns True if the new image looks like a match record. At present, supports
    PDQ shapes only.
    """
    result = (
        "ContentHash" in item_image
        and "HashType" in item_image
        and item_image["HashType"] == {"S": "pdq"}
        and "SignalSource" in item_image
        and "Quality" not in item_image
    )
    return result


def _get_keys_for_pg(pg: str) -> t.Tuple[str, str]:
    """
    Return partition and sort keys for a given privacy group.
    """


def lambda_handler(event, context):
    """
    Listens to events on the dynamodb table and increments various counters.

    Presently supported:
    ---
    1. split of hash and matches by privacy group

    Planned
    ---
    1. move total counters here
    """
    records_table = dynamodb.Table(DYNAMODB_TABLE)
    counters = defaultdict(lambda: 0)

    for record in event["Records"]:
        if record.get("eventName", "") in ("INSERT", "MODIFY"):
            # Verified that this is an insert or modify. Note that reuploads
            # come in as modifies.
            ddb_item = record["dynamodb"]["NewImage"]

            if _is_hash_record(ddb_item):
                pass  # When we do counters here, this will be useful.
            elif _is_match_record(ddb_item):
                # In theory, should be able to do this using
                # hmalib.common.aws_dataclass, but could not figure it out.
                matched_privacy_groups = list(
                    # De-Serialize ddb type to python
                    map(lambda obj: obj["S"], ddb_item["PrivacyGroups"]["L"])
                )
                for pg in matched_privacy_groups:
                    counters[pg] += 1

    logger.debug("Flushing %s", counters)
    # Flush counters to dynamodb
    MatchByPrivacyGroupCounter.increment_counts(records_table, counters)
