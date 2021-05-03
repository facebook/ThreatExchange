# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Helpers for sync privacy groups between ThreatExchange and DynamoDB
"""

from hmalib.aws_secrets import AWSSecrets
from threatexchange.api import ThreatExchangeAPI
from hmalib.common.logging import get_logger
from hmalib.common import config as hmaconfig
from hmalib.lambdas.fetcher import ThreatExchangeConfig
from botocore.exceptions import ClientError

logger = get_logger(__name__)
FETCHER_ACTIVE = True
WRITE_BACK = True


def sync_privacy_groups():
    api_key = AWSSecrets().te_api_key()
    api = ThreatExchangeAPI(api_key)
    privacy_group_member_list = api.get_threat_privacy_groups_member()
    privacy_group_owner_list = api.get_threat_privacy_groups_owner()
    unique_privacy_groups = set(privacy_group_member_list + privacy_group_owner_list)
    priavcy_group_id_in_use = set()

    for privacy_group in unique_privacy_groups:
        if privacy_group.threat_updates_enabled:
            # HMA can only read from privacy groups that have threat_updates enabled.
            # # See here for more details:
            # https://developers.facebook.com/docs/threat-exchange/reference/apis/threat-updates/v9.0
            logger.info("Adding collaboration name %s", privacy_group.name)
            priavcy_group_id_in_use.add(privacy_group.id)
            config = ThreatExchangeConfig(
                privacy_group.id,
                # TODO Currently default to True for testing purpose,
                # need to switch it to False before v0 launch
                fetcher_active=FETCHER_ACTIVE,
                privacy_group_name=privacy_group.name,
                in_use=True,
                write_back=WRITE_BACK,
            )
            try:
                hmaconfig.create_config(config)
            except ClientError as e:
                if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                    logger.warning(
                        "Can't insert duplicated config, %s",
                        e.response["Error"]["Message"],
                    )
                else:
                    raise
    update_privacy_group_in_use(priavcy_group_id_in_use)


def update_privacy_group_in_use(priavcy_group_id_in_use: set) -> None:
    collabs = ThreatExchangeConfig.get_all()
    for collab in collabs:
        if str(collab.privacy_group_id) not in priavcy_group_id_in_use:
            collab.in_use = False
            hmaconfig.update_config(collab)
