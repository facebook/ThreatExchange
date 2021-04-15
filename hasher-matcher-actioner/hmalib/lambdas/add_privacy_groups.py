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
    unique_privacy_groups = set(privacy_group_member_list + privacy_group_owner_list)
    table = dynamodb.Table(collab_config_table)
    with table.batch_writer() as batch:
        for privacy_group in unique_privacy_groups:
            if privacy_group.threat_updates_enabled:
                logger.info("Adding collaboration name %s", privacy_group.name)
                item = {
                    "Name": privacy_group.name,
                    "privacy_group": privacy_group.id,
                    "tags": [],
                    "fetcher_active": False,
                }
                batch.put_item(Item=item)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    lambda_handler(None, None)
