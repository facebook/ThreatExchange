# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Implementation of the "add_privacy_groups" module of HMA.

1. call ThreatExchange API get_threat_privacy_groups_member
and get_threat_privacy_groups_owner to get the list of privacy groups

2. If the threat_updates_enabled is true, save it to dynamoDB
"""

import os
import logging
import boto3
from hmalib.aws_secrets import AWSSecrets
from hmalib.common.logging import get_logger
from threatexchange.api import ThreatExchangeAPI


logger = get_logger(__name__)

dynamodb = boto3.resource("dynamodb")


def lambda_handler(event, context):
    collab_config_table = os.environ["THREAT_EXCHANGE_CONFIG_DYNAMODB"]
    api_key = AWSSecrets.te_api_key()
    api = ThreatExchangeAPI(api_key)
    privacy_group_member_list = api.get_threat_privacy_groups_member()
    privacy_group_owner_list = api.get_threat_privacy_groups_owner()
    items = []
    privacy_ids = set()
    build_items(items, privacy_group_member_list, privacy_ids)
    build_items(items, privacy_group_owner_list, privacy_ids)
    table = dynamodb.Table(collab_config_table)
    with table.batch_writer() as batch:
        for item in items:
            batch.put_item(Item=item)


def build_items(items, privacy_group_list, privacy_ids):
    if privacy_group_list:
        for privacy_group in privacy_group_list:
            if (
                privacy_group.threat_updates_enabled
                and privacy_group.id not in privacy_ids
            ):
                logger.info("Adding collaboration name %s", privacy_group.name)
                privacy_ids.add(privacy_group.id)
                item = {
                    "Name": privacy_group.name,
                    "privacy_group": privacy_group.id,
                    "tags": [],
                    "fetcher_active": False,
                }
                items.append(item)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    lambda_handler(None, None)
