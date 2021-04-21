# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import bottle
import typing as t
from dataclasses import dataclass, asdict
from .middleware import jsoninator, JSONifiable
from hmalib.common.config import HMAConfig
from hmalib.common import config as hmaconfig
from hmalib.lambdas.fetcher import ThreatExchangeConfig, sync_privacy_groups


@dataclass
class Dataset(JSONifiable):
    privacy_group_id: int
    privacy_group_name: str
    fetcher_active: bool

    def to_json(self) -> t.Dict:
        return asdict(self)


    @classmethod
    def from_dict(cls, d: dict) -> "Dataset":
        return cls(
            d["privacy_group_id"], d["privacy_group_name"], d["fetcher_active"]
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
                )
                for collab in collabs
            ]
        )

    @datasets_api.put("/update", apply=[jsoninator])
    def update_datasets():
        """
        Update dataset
        """
        dataSet = Dataset.from_dict(bottle.request.json)
        config = ThreatExchangeConfig(
                str(dataSet.privacy_group_id),
                fetcher_active=dataSet.fetcher_active,
                privacy_group_name=dataSet.privacy_group_name,
            )
            # Warning! Will stomp on existing configs (including if you disable them)
        hmaconfig.update_config(config)
            
        return dataSet

    @datasets_api.post("/sync", apply=[jsoninator])
    def sync_datasets():
        """
        Fetch new collaborations from ThreatExchnage and potentially update the configs stored in AWS
        """
        sync_privacy_groups()
        return SyncDatasetResponse(response="Dataset is update-to-date")

    return datasets_api
