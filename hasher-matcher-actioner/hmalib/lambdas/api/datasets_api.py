# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

from hmalib.common.count_models import MatchByPrivacyGroupCounter
import bottle
import typing as t
from dataclasses import dataclass, asdict
from mypy_boto3_dynamodb.service_resource import Table

from hmalib import metrics
from hmalib.common.config import HMAConfig
from hmalib.common import config as hmaconfig
from hmalib.common.s3_adapters import ThreatExchangeS3PDQAdapter, S3ThreatDataConfig
from hmalib.common.fetcher_models import ThreatExchangeConfig
from hmalib.common.threatexchange_config import (
    sync_privacy_groups,
    create_privacy_group_if_not_exists,
)

from .middleware import jsoninator, JSONifiable, DictParseable


@dataclass
class Dataset(JSONifiable):
    privacy_group_id: t.Union[int, str]
    privacy_group_name: str
    description: str
    fetcher_active: bool
    matcher_active: bool
    write_back: bool
    in_use: bool

    def to_json(self) -> t.Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Dataset":
        return cls(
            int(d["privacy_group_id"]),
            d["privacy_group_name"],
            d["description"],
            d["fetcher_active"],
            d["matcher_active"],
            d["write_back"],
            d["in_use"],
        )

    @classmethod
    def from_collab(cls, collab: ThreatExchangeConfig) -> "Dataset":
        return cls(
            collab.privacy_group_id,
            collab.privacy_group_name,
            collab.description,
            collab.fetcher_active,
            collab.matcher_active,
            collab.write_back,
            collab.in_use,
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


@dataclass
class DeleteDatasetResponse(JSONifiable):
    response: str

    def to_json(self) -> t.Dict:
        return asdict(self)


@dataclass
class UpdateDatasetRequest(DictParseable):
    privacy_group_id: t.Union[int, str]
    fetcher_active: bool
    matcher_active: bool
    write_back: bool

    @classmethod
    def from_dict(cls, d: dict) -> "UpdateDatasetRequest":
        return cls(
            d["privacy_group_id"],
            d["fetcher_active"],
            d["matcher_active"],
            d["write_back"],
        )


@dataclass
class CreateDatasetRequest(DictParseable):
    privacy_group_id: t.Union[int, str]
    privacy_group_name: str
    description: str
    fetcher_active: bool
    matcher_active: bool
    write_back: bool

    @classmethod
    def from_dict(cls, d: dict) -> "CreateDatasetRequest":
        return cls(
            d["privacy_group_id"],
            d["privacy_group_name"],
            d["description"],
            d["fetcher_active"],
            d["matcher_active"],
            d["write_back"],
        )


@dataclass
class CreateDatasetResponse(JSONifiable):
    response: str

    def to_json(self) -> t.Dict:
        return asdict(self)


@dataclass
class ThreatExchangeDatasetSummary(Dataset):
    """
    Factual information about a ThreatExchange dataset. This could be
    information like the name of the privacy group, the type of content it
    covers, the number of hashes it has etc.

    At the same time, it is not meant to replace the Dataset type. It will *not*
    contain configs that the user can edit. Eg. writeback_active,
    fetcher_active. Those continue to stay in the Dataset super class.
    """

    hash_count: int
    match_count: int

    def to_json(self) -> t.Dict:
        dataset_json = super().to_json()
        dataset_json.update(hash_count=self.hash_count, match_count=self.match_count)

        return dataset_json


@dataclass
class DatasetSummariesResponse(JSONifiable):
    threat_exchange_datasets: t.List[ThreatExchangeDatasetSummary]
    test_datasets: t.List[ThreatExchangeDatasetSummary]  # re-using same class for

    def to_json(self) -> t.Dict:
        return {
            "threat_exchange_datasets": [
                dataset.to_json() for dataset in self.threat_exchange_datasets
            ]
        }


def _get_signal_hash_count_and_last_modified(
    threat_exchange_data_bucket_name: str,
    threat_exchange_data_folder: str,
    threat_exchange_pdq_file_extension: str,
) -> t.Dict[str, t.Tuple[int, str]]:
    # TODO this method is expensive some cache or memoization method might be a good idea.

    s3_config = S3ThreatDataConfig(
        threat_exchange_data_bucket_name=threat_exchange_data_bucket_name,
        threat_exchange_data_folder=threat_exchange_data_folder,
        threat_exchange_pdq_file_extension=threat_exchange_pdq_file_extension,
    )
    pdq_storage = ThreatExchangeS3PDQAdapter(
        config=s3_config, metrics_logger=metrics.names.api_hash_count()
    )
    pdq_data_files = pdq_storage.load_data()
    return {
        file_name: (len(rows), pdq_storage.last_modified[file_name])
        for file_name, rows in pdq_data_files.items()
    }


def _get_threat_exchange_datasets(
    table: Table,
    threat_exchange_data_bucket_name: str,
    threat_exchange_data_folder: str,
    threat_exchange_pdq_file_extension: str,
) -> t.List[ThreatExchangeDatasetSummary]:
    collaborations = ThreatExchangeConfig.get_all()
    hash_counts: t.Dict[
        str, t.Tuple[int, str]
    ] = _get_signal_hash_count_and_last_modified(
        threat_exchange_data_bucket_name,
        threat_exchange_data_folder,
        threat_exchange_pdq_file_extension,
    )

    match_counts: t.Dict[str, int] = MatchByPrivacyGroupCounter.get_all_counts(table)

    return [
        ThreatExchangeDatasetSummary(
            collab.privacy_group_id,
            collab.privacy_group_name,
            collab.description,
            collab.fetcher_active,
            collab.matcher_active,
            collab.write_back,
            collab.in_use,
            hash_count=t.cast(
                int,
                hash_counts.get(
                    f"{threat_exchange_data_folder}{collab.privacy_group_id}{threat_exchange_pdq_file_extension}",
                    [0, ""],
                )[0],
            ),
            match_count=match_counts.get(collab.privacy_group_id, 0),
        )
        for collab in collaborations
    ]


def get_datasets_api(
    hma_config_table: str,
    datastore_table: Table,
    threat_exchange_data_bucket_name: str,
    threat_exchange_data_folder: str,
    threat_exchange_pdq_file_extension: str,
) -> bottle.Bottle:
    # The documentation below expects prefix to be '/datasets/'
    datasets_api = bottle.Bottle()
    HMAConfig.initialize(hma_config_table)

    @datasets_api.get("/", apply=[jsoninator])
    def get_all_dataset_summaries() -> DatasetSummariesResponse:
        """
        Returns summaries for all datasets. Summary includes all facts that are
        not configurable. Eg. its name, the number of hashes it has, the
        number of matches it has caused, etc.
        """
        return DatasetSummariesResponse(
            threat_exchange_datasets=_get_threat_exchange_datasets(
                datastore_table,
                threat_exchange_data_bucket_name,
                threat_exchange_data_folder,
                threat_exchange_pdq_file_extension,
            ),
            test_datasets=[],
        )

    @datasets_api.post("/update", apply=[jsoninator(UpdateDatasetRequest)])
    def update_dataset(request: UpdateDatasetRequest) -> Dataset:
        """
        Update dataset fetcher_active, write_back and matcher_active
        """
        config = ThreatExchangeConfig.getx(str(request.privacy_group_id))
        config.fetcher_active = request.fetcher_active
        config.write_back = request.write_back
        config.matcher_active = request.matcher_active
        updated_config = hmaconfig.update_config(config).__dict__
        updated_config["privacy_group_id"] = updated_config["name"]
        return Dataset.from_dict(updated_config)

    @datasets_api.post("/create", apply=[jsoninator(CreateDatasetRequest)])
    def create_dataset(request: CreateDatasetRequest) -> CreateDatasetResponse:
        """
        Create a local dataset (defaults defined in CreateDatasetRequest)
        """
        assert isinstance(request, CreateDatasetRequest)

        create_privacy_group_if_not_exists(
            privacy_group_id=str(request.privacy_group_id),
            privacy_group_name=request.privacy_group_name,
            description=request.description,
            in_use=True,
            fetcher_active=request.fetcher_active,
            matcher_active=request.matcher_active,
            write_back=request.write_back,
        )

        return CreateDatasetResponse(
            response=f"Created dataset {request.privacy_group_id}"
        )

    @datasets_api.post("/sync", apply=[jsoninator])
    def sync_datasets() -> SyncDatasetResponse:
        """
        Fetch new collaborations from ThreatExchnage and potentially update the configs stored in AWS
        """
        sync_privacy_groups()
        return SyncDatasetResponse(response="Privacy groups are up to date")

    @datasets_api.post("/delete/<key>", apply=[jsoninator])
    def delete_dataset(key=None) -> DeleteDatasetResponse:
        """
        Delete dataset
        """
        config = ThreatExchangeConfig.getx(str(key))
        hmaconfig.delete_config(config)
        return DeleteDatasetResponse(response="The privacy group is deleted")

    return datasets_api
