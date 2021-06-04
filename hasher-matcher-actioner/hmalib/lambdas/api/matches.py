# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import bottle
import datetime

from dataclasses import dataclass, asdict
from mypy_boto3_dynamodb.service_resource import Table
import typing as t
from enum import Enum
from logging import Logger

from threatexchange.descriptor import ThreatDescriptor
from hmalib.models import PDQMatchRecord
from hmalib.common.signal_models import PDQSignalMetadata, PendingOpinionChange
from hmalib.common.logging import get_logger
from hmalib.common.message_models import BankedSignal, WritebackMessage, WritebackTypes
from .middleware import jsoninator, JSONifiable
from hmalib.common.config import HMAConfig

logger = get_logger(__name__)


@dataclass
class MatchSummary(JSONifiable):
    content_id: str
    signal_id: t.Union[str, int]
    signal_source: str
    updated_at: str

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
    dataset: str
    tags: t.List[str]
    opinion: str
    pending_opinion_change: str

    def to_json(self) -> t.Dict:
        return asdict(self)


@dataclass
class MatchDetail(JSONifiable):
    content_id: str
    content_hash: str
    signal_id: t.Union[str, int]
    signal_hash: str
    signal_source: str
    signal_type: str
    updated_at: str
    metadata: t.List[MatchDetailMetadata]

    def to_json(self) -> t.Dict:
        result = asdict(self)
        result.update(metadata=[datum.to_json() for datum in self.metadata])
        return result


@dataclass
class MatchDetailsResponse(JSONifiable):
    match_details: t.List[MatchDetail]

    def to_json(self) -> t.Dict:
        return {"match_details": [detail.to_json() for detail in self.match_details]}


@dataclass
class ChangeSignalOpinionResponse(JSONifiable):
    success: bool

    def to_json(self) -> t.Dict:
        return {"change_requested": self.success}


def get_match_details(
    table: Table, content_id: str, image_folder_key: str
) -> t.List[MatchDetail]:
    if not content_id:
        return []

    records = PDQMatchRecord.get_from_content_id(
        table, f"{image_folder_key}{content_id}"
    )

    return [
        MatchDetail(
            content_id=record.content_id[len(image_folder_key) :],
            content_hash=record.content_hash,
            signal_id=record.signal_id,
            signal_hash=record.signal_hash,
            signal_source=record.signal_source,
            signal_type=record.SIGNAL_TYPE,
            updated_at=record.updated_at.isoformat(),
            metadata=get_signal_details(table, record.signal_id, record.signal_source),
        )
        for record in records
    ]


def get_signal_details(
    table: Table, signal_id: t.Union[str, int], signal_source: str
) -> t.List[MatchDetailMetadata]:
    if not signal_id or not signal_source:
        return []

    return [
        MatchDetailMetadata(
            dataset=metadata.ds_id,
            tags=[
                tag for tag in metadata.tags if tag not in ThreatDescriptor.SPECIAL_TAGS
            ],
            opinion=get_opinion_from_tags(metadata.tags).value,
            pending_opinion_change=metadata.pending_opinion_change.value,
        )
        for metadata in PDQSignalMetadata.get_from_signal(
            table, signal_id, signal_source
        )
    ]


class OpinionString(Enum):
    TRUE_POSITIVE = "True Positive"
    FALSE_POSITIVE = "False Positive"
    DISPUTED = "Disputed"
    UNKNOWN = "Unknown"


def get_opinion_from_tags(tags: t.List[str]) -> OpinionString:
    # see python-threatexchange descriptor.py for origins
    if ThreatDescriptor.TRUE_POSITIVE in tags:
        return OpinionString.TRUE_POSITIVE
    if ThreatDescriptor.FALSE_POSITIVE in tags:
        return OpinionString.FALSE_POSITIVE
    if ThreatDescriptor.DISPUTED in tags:
        return OpinionString.DISPUTED
    return OpinionString.UNKNOWN


def get_matches_api(
    dynamodb_table: Table, image_folder_key: str, hma_config_table: str
) -> bottle.Bottle:
    """
    A Closure that includes all dependencies that MUST be provided by the root
    API that this API plugs into. Declare dependencies here, but initialize in
    the root API alone.
    """

    # A prefix to all routes must be provided by the api_root app
    # The documentation below expects prefix to be '/matches/'
    matches_api = bottle.Bottle()
    HMAConfig.initialize(hma_config_table)

    @matches_api.get("/", apply=[jsoninator])
    def matches() -> MatchSummariesResponse:
        """
        Returns all, or a filtered list of matches.
        """
        signal_q = bottle.request.query.signal_q or None
        signal_source = bottle.request.query.signal_source or None
        content_q = bottle.request.query.content_q or None

        if content_q:
            records = PDQMatchRecord.get_from_content_id(dynamodb_table, content_q)
        elif signal_q:
            records = PDQMatchRecord.get_from_signal(
                dynamodb_table, signal_q, signal_source or ""
            )
        else:
            records = PDQMatchRecord.get_from_time_range(dynamodb_table)

        return MatchSummariesResponse(
            match_summaries=[
                MatchSummary(
                    content_id=record.content_id[len(image_folder_key) :],
                    signal_id=record.signal_id,
                    signal_source=record.signal_source,
                    updated_at=record.updated_at.isoformat(),
                )
                for record in records
            ]
        )

    @matches_api.get("/match/", apply=[jsoninator])
    def match_details() -> MatchDetailsResponse:
        """
        match details API endpoint:
        return format: match_details : [MatchDetailsResult]
        """
        results = []
        if content_id := bottle.request.query.content_id or None:
            results = get_match_details(dynamodb_table, content_id, image_folder_key)
        return MatchDetailsResponse(match_details=results)

    @matches_api.post("/request-signal-opinion-change/")
    def request_signal_opinion_change() -> ChangeSignalOpinionResponse:
        """
        request a change to the opinion for a signal in a dataset
        """
        signal_id = bottle.request.query.signal_q or None
        signal_source = bottle.request.query.signal_source or None
        ds_id = bottle.request.query.dataset_q or None
        opinion_change = bottle.request.query.opinion_change or None

        if not signal_id or not signal_source or not ds_id or not opinion_change:
            return ChangeSignalOpinionResponse(False)

        signal_id = str(signal_id)
        pending_opinion_change = PendingOpinionChange(opinion_change)

        writeback_message = WritebackMessage.from_banked_signal_and_opinion_change(
            BankedSignal(signal_id, ds_id, signal_source), pending_opinion_change
        )
        writeback_message.send_to_queue()
        logger.info(
            f"Opinion change enqueued for {signal_source}:{signal_id} in {ds_id} change={opinion_change}"
        )

        signal = PDQSignalMetadata(
            signal_id=signal_id,
            ds_id=ds_id,
            updated_at=datetime.datetime.now(),
            signal_source=signal_source,
            signal_hash="",  # SignalHash not needed for update
            tags=[],  # Tags not needed for update
            pending_opinion_change=pending_opinion_change,
        )
        success = signal.update_pending_opinion_change_in_table_if_exists(
            dynamodb_table
        )
        if not success:
            logger.info(f"Attempting to update {signal} in db failed")

        return ChangeSignalOpinionResponse(success)

    return matches_api
