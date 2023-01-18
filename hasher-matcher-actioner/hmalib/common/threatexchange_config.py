# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Helpers for sync privacy groups between ThreatExchange and DynamoDB
"""
from botocore.exceptions import ClientError
from requests.exceptions import HTTPError

from threatexchange.exchanges.clients.fb_threatexchange.api import ThreatExchangeAPI

from hmalib.aws_secrets import AWSSecrets
from hmalib.common.logging import get_logger
from hmalib.common import config as hmaconfig
from hmalib.common.configs.fetcher import ThreatExchangeConfig

logger = get_logger(__name__)

# TODO Currently default to True for testing purpose,
# need to switch it to False before v0 launch
FETCHER_ACTIVE_DEFAULT = False
WRITE_BACK_DEFAULT = False
MATCHER_ACTIVE_DEFAULT = True
SAMPLE_DATASET_PRIVACY_GROUP_ID = ["inria-holidays-test"]


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


def sync_privacy_groups(secrets_prefix: str):
    api_token = AWSSecrets(prefix=secrets_prefix).te_api_token()
    api = ThreatExchangeAPI(api_token)
    privacy_group_member_list = api.get_threat_privacy_groups_member()
    privacy_group_owner_list = api.get_threat_privacy_groups_owner()
    unique_privacy_groups = set(privacy_group_member_list + privacy_group_owner_list)
    priavcy_group_id_in_use = set(
        SAMPLE_DATASET_PRIVACY_GROUP_ID
    )  # add sample test dataset id to avoid disable it when syncing from HMA UI

    for privacy_group in unique_privacy_groups:
        if privacy_group.threat_updates_enabled:
            # HMA can only read from privacy groups that have threat_updates enabled.
            # # See here for more details:
            # https://developers.facebook.com/docs/threat-exchange/reference/apis/threat-updates/v9.0
            priavcy_group_id_in_use.add(str(privacy_group.id))
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


def try_api_token(api_token: str) -> bool:
    """
    Try the new API token to make a get_privacy_groups member call. If
    successful, return True, else False.

    Some doctests to choose from:
    >>> from hmalib.common.threatexchange_config import try_api_token
    >>> try_api_token("<valid token>")
    True
    >>> try_api_token("<blank_string>")
    False
    >>> try_api_token("<invalid_token>")
    False
    """
    api = ThreatExchangeAPI(api_token)
    try:
        api.get_threat_privacy_groups_member()
        return True
    except (ValueError, HTTPError):
        return False
