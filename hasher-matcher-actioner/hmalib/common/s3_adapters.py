# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import os
import boto3
import csv
import codecs

import typing as t

from dataclasses import dataclass
from hmalib import metrics
from hmalib.common.logging import get_logger

logger = get_logger(__name__)

s3_client = boto3.client("s3")
HashRowT = t.Tuple[str, t.Dict[str, t.Any]]


@dataclass
class S3ThreatDataConfig:

    threat_exchange_data_bucket_name: str
    threat_exchange_data_folder: str
    threat_exchange_pdq_file_extension: str


@dataclass
class ThreatExchangeS3Adapter:
    """
    Adapter for reading ThreatExchange data stored in S3. Concrete implementations
    are for a specific indicator type such as PDQ

    Assumes CSV file format

    Should probably refactor and merge with ThreatUpdateS3Store for writes
    """

    metrics_logger: metrics.lambda_with_datafiles

    S3FileT = t.Dict[str, t.Any]
    config: S3ThreatDataConfig

    def load_data(self) -> t.Dict[str, t.List[HashRowT]]:
        """
        loads all data from all files in TE that are of the concrete implementations indicator type

        returns a mapping from file name to list of rows
        """
        logger.info("Retreiving %s Data from S3", self.file_type_str_name)
        with metrics.timer(self.metrics_logger.download_datafiles):
            # S3 doesnt have a built in concept of folders but the AWS UI
            # implements folder-like functionality using prefixes. We follow
            # this same convension here using folder name in a prefix search
            s3_bucket_files = s3_client.list_objects_v2(
                Bucket=self.config.threat_exchange_data_bucket_name,
                Prefix=self.config.threat_exchange_data_folder,
            )["Contents"]
            logger.info("Found %d Files", len(s3_bucket_files))

            typed_data_files = {
                file["Key"]: self._get_file(file["Key"])
                for file in s3_bucket_files
                if file["Key"].endswith(self.indicator_type_file_extension)
            }
            logger.info(
                "Found %d %s Files", len(typed_data_files), self.file_type_str_name
            )

        with metrics.timer(self.metrics_logger.parse_datafiles):
            logger.info("Parsing %s Hash files", self.file_type_str_name)
            typed_data = {
                file_name: self._parse_file(**typed_data_file)
                for file_name, typed_data_file in typed_data_files.items()
            }
        return typed_data

    @property
    def indicator_type_file_extension(self):
        """
        What is the extension for files of this indicator type

        eg. pdq.te indicates PDQ files
        """
        raise NotImplementedError()

    @property
    def file_type_str_name(self):
        """
        What types of files does the concrete implementation correspond to

        for logging only
        """
        raise NotImplementedError()

    @property
    def indicator_type_file_columns(self):
        """
        What are the csv columns when this type of data is stored in S3
        """
        raise NotImplementedError()

    def _get_file(self, file_name: str) -> t.Dict[str, t.Any]:
        return {
            "file_name": file_name,
            "data_file": s3_client.get_object(
                Bucket=self.config.threat_exchange_data_bucket_name, Key=file_name
            ),
        }

    def _parse_file(self, file_name: str, data_file: S3FileT) -> t.List[HashRowT]:
        data_reader = csv.DictReader(
            codecs.getreader("utf-8")(data_file["Body"]),
            fieldnames=self.indicator_type_file_columns,
        )
        privacy_group = file_name.split("/")[-1].split(".")[0]
        return [
            (
                row["hash"],
                # Also add hash to metadata for easy look up on match
                {
                    "id": int(row["id"]),
                    "hash": row["hash"],
                    "source": "te",  # default for now to make downstream easier to generalize
                    "privacy_groups": set(
                        [privacy_group]
                    ),  # read privacy group from key
                    "tags": {privacy_group: row["tags"].split(" ")}
                    if row["tags"]
                    else {},  # note: these are the labels assigned by pytx in descriptor.py (NOT a 1-1 with tags on TE)
                },
            )
            for row in data_reader
        ]


class ThreatExchangeS3PDQAdapter(ThreatExchangeS3Adapter):
    """
    Adapter for reading ThreatExchange PDQ data stored in CSV files S3
    """

    @property
    def indicator_type_file_extension(self):
        return self.config.threat_exchange_pdq_file_extension

    @property
    def indicator_type_file_columns(self):
        return ["hash", "id", "timestamp", "tags"]

    @property
    def file_type_str_name(self):
        return "PDQ"
