# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import bottle
import typing as t
from dataclasses import dataclass, asdict
from hmalib.aws_secrets import AWSSecrets
from threatexchange.api import ThreatExchangeAPI
from hmalib.common.logging import get_logger
from .middleware import jsoninator, JSONifiable
from hmalib.common.config import HMAConfig
from hmalib.common import config as hmaconfig
from hmalib.lambdas.fetcher import ThreatExchangeConfig

logger = get_logger(__name__)


@dataclass
class Dataset(JSONifiable):
    privacy_group_id: int
    privacy_group_name: str
    fetcher_active: bool
    write_back: bool
    in_use: bool

    def to_json(self) -> t.Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Dataset":
        return cls(
            d["privacy_group_id"],
            d["privacy_group_name"],
            d["fetcher_active"],
            d["write_back"],
            d["in_use"],
        )


@dataclass
class DatasetsResponse(JSONifiable):
    datasets_response: t.List[Dataset]

    def to_json(self) -> t.Dict:
        return {
            "datasets_response": [
                dataset.to_json() for dataset in self.datasets_response
            ]
        }


@dataclass
class SyncDatasetResponse(JSONifiable):
    response: str

    def to_json(self) -> t.Dict:
        return asdict(self)


def sync_privacy_groups():
    """
    Implementation of the "sync_privacy_groups" function of threatexchange config.

    1. call ThreatExchange API get_threat_privacy_groups_member
    and get_threat_privacy_groups_owner to get the list of privacy groups

    2. If the threat_updates_enabled is true, save it using config framework if it doesn't
    exist in dynamoDB.

    3. If one privacy group exists in dynamoDB but not in the result of get_threat_privacy_groups_owner
    or get_threat_privacy_groups_member, update in_user to false
    """
    api_key = AWSSecrets.te_api_key()
    api = ThreatExchangeAPI(api_key)
    privacy_group_member_list = api.get_threat_privacy_groups_member()
    privacy_group_owner_list = api.get_threat_privacy_groups_owner()
    unique_privacy_groups = set(privacy_group_member_list + privacy_group_owner_list)

    for privacy_group in unique_privacy_groups:
        if privacy_group.threat_updates_enabled:
            # HMA can only read from privacy groups that have threat_updates enabled.
            # # See here for more details:
            # https://developers.facebook.com/docs/threat-exchange/reference/apis/threat-updates/v9.0
            logger.info("Adding collaboration name %s", privacy_group.name)
            config = ThreatExchangeConfig(
                privacy_group.id,
                # TODO Currently default to True for testing purpose,
                # need to switch it to False before v0 launch
                fetcher_active=True,
                privacy_group_name=privacy_group.name,
                in_use=True,
                write_back=False,
            )
            # Warning! Will stomp on existing configs (including if you disable them)
            # TODO need to compare with existing privacy groups in dynamoDB to create/update/delete
            hmaconfig.update_config(config, insert_only=True)


def get_datasets_api(hma_config_table: str) -> bottle.Bottle:
    """
    A Closure that includes all dependencies that MUST be provided by the root
    API that this API plugs into. Declare dependencies here, but initialize in
    the root API alone.
    """

    # A prefix to all routes must be provided by the api_root app
    # The documentation below expects prefix to be '/datasets/'
    datasets_api = bottle.Bottle()
    HMAConfig.initialize(hma_config_table)

    @datasets_api.get("/", apply=[jsoninator])
    def datasets() -> DatasetsResponse:
        """
        Returns all datasets.
        """
        collabs = ThreatExchangeConfig.get_all()
        return DatasetsResponse(
            datasets_response=[
                Dataset(
                    privacy_group_id=collab.privacy_group_id,
                    privacy_group_name=collab.privacy_group_name,
                    fetcher_active=collab.fetcher_active,
                    write_back=collab.write_back,
                    in_use=collab.in_use,
                )
                for collab in collabs
            ]
        )

    @datasets_api.put("/update", apply=[jsoninator])
    def update_datasets():
        """
        Update dataset
        """
        dataset = bottle.request.json
        updates = {}
        if dataset["fetcher_active"] is not None:
            updates["fetcher_active"] = dataset["fetcher_active"]
        if dataset["write_back"] is not None:
            updates["write_back"] = dataset["write_back"]
        # Will only insert the item if privacy_group_id didn't exist
        updated_dataset = hmaconfig.update_config_attributes_by_type_and_name(
            config_type="ThreatExchangeConfig",
            name=str(dataset["privacy_group_id"]),
            updates=updates,
        )
        updated_dataset["privacy_group_id"] = int(updated_dataset["ConfigName"])
        return Dataset.from_dict(updated_dataset)

    @datasets_api.post("/sync", apply=[jsoninator])
    def sync_datasets():
        """
        Fetch new collaborations from ThreatExchnage and potentially update the configs stored in AWS
        """
        sync_privacy_groups()
        return SyncDatasetResponse(response="Dataset is update-to-date")

    return datasets_api
