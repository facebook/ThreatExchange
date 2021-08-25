# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import json
import boto3
import bottle
import datetime
import functools
import dataclasses

from dataclasses import dataclass, asdict
from mypy_boto3_dynamodb.service_resource import Table
import typing as t
from enum import Enum
from logging import Logger
from mypy_boto3_sqs.client import SQSClient

from threatexchange.descriptor import ThreatDescriptor

from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.pdq import PdqSignal

from hmalib.common.models.pipeline import MatchRecord
from hmalib.common.models.signal import (
    ThreatExchangeSignalMetadata,
    PendingThreatExchangeOpinionChange,
)
from hmalib.common.logging import get_logger
from hmalib.common.messages.match import BankedSignal
from hmalib.common.messages.writeback import WritebackMessage
from .middleware import jsoninator, JSONifiable, DictParseable
from hmalib.common.config import HMAConfig
from hmalib.matchers.matchers_base import Matcher


logger = get_logger(__name__)


@functools.lru_cache(maxsize=None)
def _get_sqs_client() -> SQSClient:
    return boto3.client("sqs")


@functools.lru_cache(maxsize=None)
def _get_matcher(index_bucket_name: str) -> Matcher:
    return Matcher(
        index_bucket_name=index_bucket_name,
        supported_signal_types=[PdqSignal, VideoMD5Signal],
    )


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
class ThreatExchangeMatchDetailMetadata(JSONifiable):
    privacy_group_id: str
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
    metadata: t.List[ThreatExchangeMatchDetailMetadata]

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


def get_match_details(table: Table, content_id: str) -> t.List[MatchDetail]:
    if not content_id:
        return []

    records = MatchRecord.get_from_content_id(table, f"{content_id}")

    return [
        MatchDetail(
            content_id=record.content_id,
            content_hash=record.content_hash,
            signal_id=record.signal_id,
            signal_hash=record.signal_hash,
            signal_source=record.signal_source,
            signal_type=record.signal_type.get_name(),
            updated_at=record.updated_at.isoformat(),
            metadata=get_signal_details(table, record.signal_id, record.signal_source),
        )
        for record in records
    ]


def get_signal_details(
    table: Table, signal_id: t.Union[str, int], signal_source: str
) -> t.List[ThreatExchangeMatchDetailMetadata]:
    # TODO: Remove need for signal_source. That's part of the *SignalMetadata class now.
    if not signal_id or not signal_source:
        return []

    return [
        ThreatExchangeMatchDetailMetadata(
            privacy_group_id=metadata.privacy_group_id,
            tags=[
                tag for tag in metadata.tags if tag not in ThreatDescriptor.SPECIAL_TAGS
            ],
            opinion=get_opinion_from_tags(metadata.tags).value,
            pending_opinion_change=metadata.pending_opinion_change.value,
        )
        for metadata in ThreatExchangeSignalMetadata.get_from_signal(table, signal_id)
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


@dataclass
class MatchesForHashRequest(DictParseable):
    signal_value: str
    signal_type: str

    @classmethod
    def from_dict(cls, d):
        # todo translate signal type to actual type
        return cls(**{f.name: d.get(f.name, None) for f in dataclasses.fields(cls)})


@dataclass
class MatchesForHashResponse(JSONifiable):
    matches: t.List[t.Union[ThreatExchangeSignalMetadata]]
    signal_value: str

    def to_json(self) -> t.Dict:
        return {"matches": [match.to_json() for match in self.matches]}


def get_matches_api(
    dynamodb_table: Table,
    hma_config_table: str,
    indexes_bucket_name: str,
    writeback_queue_url: str,
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
            records = MatchRecord.get_from_content_id(dynamodb_table, content_q)
        elif signal_q:
            records = MatchRecord.get_from_signal(
                dynamodb_table, signal_q, signal_source or ""
            )
        else:
            # TODO: Support pagination after implementing in UI.
            records = MatchRecord.get_recent_items_page(dynamodb_table).items

        return MatchSummariesResponse(
            match_summaries=[
                MatchSummary(
                    content_id=record.content_id,
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
            results = get_match_details(dynamodb_table, content_id)
        return MatchDetailsResponse(match_details=results)

    @matches_api.post("/request-signal-opinion-change/", apply=[jsoninator])
    def request_signal_opinion_change() -> ChangeSignalOpinionResponse:
        """
        request a change to the opinion for a signal in a dataset
        """
        signal_id = bottle.request.query.signal_id or None
        signal_source = bottle.request.query.signal_source or None
        privacy_group_id = bottle.request.query.privacy_group_id or None
        opinion_change = bottle.request.query.opinion_change or None

        if (
            not signal_id
            or not signal_source
            or not privacy_group_id
            or not opinion_change
        ):
            return ChangeSignalOpinionResponse(False)

        signal_id = str(signal_id)
        pending_opinion_change = PendingThreatExchangeOpinionChange(opinion_change)

        writeback_message = WritebackMessage.from_banked_signal_and_opinion_change(
            BankedSignal(signal_id, privacy_group_id, signal_source),
            pending_opinion_change,
        )
        writeback_message.send_to_queue(_get_sqs_client(), writeback_queue_url)
        logger.info(
            f"Opinion change enqueued for {signal_source}:{signal_id} in {privacy_group_id} change={opinion_change}"
        )

        signal = ThreatExchangeSignalMetadata.get_from_signal_and_privacy_group(
            dynamodb_table, signal_id=signal_id, privacy_group_id=privacy_group_id
        )

        if not signal:
            logger.error("Signal not found.")

        signal = t.cast(ThreatExchangeSignalMetadata, signal)
        signal.pending_opinion_change = pending_opinion_change
        success = signal.update_pending_opinion_change_in_table_if_exists(
            dynamodb_table
        )

        if not success:
            logger.error(f"Attempting to update {signal} in db failed")

        return ChangeSignalOpinionResponse(success)

    @matches_api.get("/for-hash/", apply=[jsoninator(MatchesForHashRequest)])
    def for_hash(request: MatchesForHashRequest) -> MatchesForHashResponse:
        """
        For a given hash/signal check the index(es) for matches and return the details
        NOTE: currently metadata returned will not be written to the dynamodb table
        unlike in the case of a pipeline match based on submissions.
        """
        signal_type = None
        if request.signal_type == "pdq":
            # todo translate in MatchesForHashRequest and extend to cover MD5
            signal_type = PdqSignal

        if not signal_type:
            # only support PDQ at the moment
            bottle.response.status = 400
            return MatchesForHashResponse([], request.signal_value)

        matches = _get_matcher(indexes_bucket_name).match(
            signal_type, request.signal_value
        )

        match_objects = []

        for match in matches:
            match_objects.extend(
                Matcher.get_metadata_objects_from_match(signal_type, match)
            )

        return MatchesForHashResponse(match_objects, request.signal_value)

    return matches_api
