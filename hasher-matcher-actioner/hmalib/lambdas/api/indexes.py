# Copyright (c) Meta Platforms, Inc. and affiliates.

import functools
import boto3
import typing as t
import bottle
import datetime
from dataclasses import dataclass

from mypy_boto3_lambda.client import LambdaClient

from hmalib.indexers.index_store import S3PickledIndexStore
from hmalib.lambdas.api.middleware import SubApp, jsoninator


@functools.lru_cache(maxsize=None)
def _get_lambda_client() -> LambdaClient:
    return boto3.client("lambda")


@dataclass
class IndexesLastModifiedResponse:
    last_modified: datetime.datetime

    def to_json(self) -> t.Dict[str, str]:
        return {
            "last_modified": self.last_modified.isoformat(),
        }


def get_indexes_api(
    indexes_bucket_name: str, indexer_function_name: str
) -> bottle.Bottle:
    indexes_api = SubApp()

    @indexes_api.get("/last-modified", apply=[jsoninator])
    def all_indexes_last_modified() -> IndexesLastModifiedResponse:
        """
        Returns the max of last_modified time of all indexes. Read as: when was
        the latest index rebuilt.
        """
        index_store = S3PickledIndexStore(indexes_bucket_name)
        return IndexesLastModifiedResponse(index_store.get_latest_last_modified())

    @indexes_api.post("/rebuild-all")
    def rebuild_all_indexes():
        """
        Well, it rebuilds all your indexes. Async operation. Just triggers, does
        not wait.
        """
        response = _get_lambda_client().invoke(
            FunctionName=indexer_function_name,
            InvocationType="Event",
        )

    return indexes_api
