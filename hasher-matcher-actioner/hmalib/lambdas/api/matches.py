# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import bottle
from dataclasses import dataclass, asdict
import os
from mypy_boto3_dynamodb.service_resource import Table
import typing as t

from hmalib.models import PDQMatchRecord
from .middleware import jsoninator, JSONifiable


# TODO: Remove dependency on image folder key, use a common interface for
# s3 and non-s3 HMA requests.
IMAGE_FOLDER_KEY = os.environ["IMAGE_FOLDER_KEY"]
IMAGE_FOLDER_KEY_LEN = len(IMAGE_FOLDER_KEY)


@dataclass
class MatchSummary(JSONifiable):
    content_id: str
    signal_id: t.Union[str, int]
    signal_source: str
    updated_at: str
    reactions: str

    def to_json(self) -> t.Dict:
        return asdict(self)


@dataclass
class MatchSummariesResponse(JSONifiable):
    match_summaries: t.List[MatchSummary]

    def to_json(self) -> t.Dict:
        return {
            "match_summaries": [summary.to_json() for summary in self.match_summaries]
        }


@dataclass
class MatchDetailMetadata(JSONifiable):
    type: str
    tags: t.List[str]
    status: str
    opinions: t.List[str]

    def to_json(self) -> t.Dict:
        return asdict(self)


@dataclass
class MatchDetail(JSONifiable):
    content_id: str
    content_hash: str
    signal_id: t.Union[str, int]
    signal_hash: str
    signal_source: str
    updated_at: str
    meta_data: MatchDetailMetadata
    actions: t.List[str]

    def to_json(self) -> t.Dict:
        result = asdict(self)
        result.update(meta_data=self.meta_data.to_json())
        return result


@dataclass
class MatchDetailsResponse(JSONifiable):
    match_details: t.List[MatchDetail]

    def to_json(self) -> t.Dict:
        return {"match_details": [detail.to_json() for detail in self.match_details]}


def get_match_details(table: Table, content_id: str) -> t.List[MatchDetail]:
    if not content_id:
        return []

    records = PDQMatchRecord.get_from_content_id(
        table, f"{IMAGE_FOLDER_KEY}{content_id}"
    )

    # TODO these mocked metadata should either be added to
    # PDQMatchRecord or some other look up in the data model
    mocked_metadata = MatchDetailMetadata(
        type="HASH_PDQ",
        tags=["mocked_t1", "mocked_t2"],
        status="MOCKED_STATUS",
        opinions=["mocked_a1", "mocked_a2"],
    )

    mocked_actions = ["Mocked_False_Postive", "Mocked_Delete"]
    return [
        MatchDetail(
            content_id=record.content_id[IMAGE_FOLDER_KEY_LEN:],
            content_hash=record.content_hash,
            signal_id=record.signal_id,
            signal_hash=record.signal_hash,
            signal_source=record.signal_source,
            updated_at=record.updated_at.isoformat(),
            meta_data=mocked_metadata,
            actions=mocked_actions,
        )
        for record in records
    ]


def get_matches_api(dynamodb_table: Table) -> bottle.Bottle:
    """
    A Closure that includes all dependencies that MUST be provided by the root
    API that this API plugs into. Declare dependencies here, but initialize in
    the root API alone.
    """

    # A prefix to all routes must be provided by the api_root app
    # The documentation below expects prefix to be '/matches/v1'
    matches_api = bottle.Bottle()

    @matches_api.get("/matches/", apply=[jsoninator])
    def matches() -> MatchSummariesResponse:
        """
        Returns all, or a filtered list of matches.
        """
        records = PDQMatchRecord.get_from_time_range(dynamodb_table)
        return MatchSummariesResponse(
            match_summaries=[
                MatchSummary(
                    content_id=record.content_id[IMAGE_FOLDER_KEY_LEN:],
                    signal_id=record.signal_id,
                    signal_source=record.signal_source,
                    updated_at=record.updated_at.isoformat(),
                    reactions="Mocked",
                )
                for record in records
            ]
        )

    @matches_api.get("/match/<key>/", apply=[jsoninator])
    def match_details(key=None) -> MatchDetailsResponse:
        """
        matche details API endpoint:
        return format: match_details : [MatchDetailsResult]
        """
        results = get_match_details(dynamodb_table, key)
        return MatchDetailsResponse(match_details=results)

    return matches_api