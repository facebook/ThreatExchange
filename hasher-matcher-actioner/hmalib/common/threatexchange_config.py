# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Helpers for sync privacy groups between ThreatExchange and DynamoDB
"""

from hmalib.aws_secrets import AWSSecrets
from threatexchange.api import ThreatExchangeAPI
from hmalib.common.logging import get_logger
from hmalib.common import config as hmaconfig
from hmalib.common.config import HMAConfig
from hmalib.common.fetcher_models import ThreatExchangeConfig
from botocore.exceptions import ClientError

logger = get_logger(__name__)

# TODO Currently default to True for testing purpose,
# need to switch it to False before v0 launch
FETCHER_ACTIVE_DEFAULT = True
WRITE_BACK_DEFAULT = True
MATCHER_ACTIVE_DEFAULT = True


def create_privacy_group_if_not_exists(
    privacy_group_id: str,
    privacy_group_name: str,
    description: str = "",
    in_use: bool = True,
    fetcher_active: bool = FETCHER_ACTIVE_DEFAULT,
    matcher_active: bool = MATCHER_ACTIVE_DEFAULT,
    write_back: bool = WRITE_BACK_DEFAULT,
):
    logger.info("Adding collaboration name %s", privacy_group_name)
    config = ThreatExchangeConfig(
        privacy_group_id,
        fetcher_active=fetcher_active,
        privacy_group_name=privacy_group_name,
        in_use=in_use,
        description=description,
        matcher_active=matcher_active,
        write_back=write_back,
    )
    try:
        hmaconfig.create_config(config)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            logger.warning(
                "Can't insert duplicated config, %s",
                e.response["Error"]["Message"],
            )
            if description:
                update_privacy_group_description(privacy_group_id, description)
        else:
            raise


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
            priavcy_group_id_in_use.add(privacy_group.id)
            create_privacy_group_if_not_exists(
                str(privacy_group.id),
                privacy_group_name=privacy_group.name,
                description=privacy_group.description,
            )
    update_privacy_groups_in_use(priavcy_group_id_in_use)


def update_privacy_group_description(privacy_group_id: str, description: str) -> None:
    config = ThreatExchangeConfig.getx(privacy_group_id)
    config.description = description
    hmaconfig.update_config(config)


def update_privacy_groups_in_use(priavcy_group_id_in_use: set) -> None:
    collabs = ThreatExchangeConfig.get_all()
    for collab in collabs:
        if str(collab.privacy_group_id) not in priavcy_group_id_in_use:
            collab.in_use = False
            hmaconfig.update_config(collab)
