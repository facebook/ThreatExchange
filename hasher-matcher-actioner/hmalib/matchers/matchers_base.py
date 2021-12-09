# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Implements a unified matcher class. The unified matcher is capable of matching
against any index defined in python-threatexchange.
"""

import datetime
import functools

from mypy_boto3_sns.client import SNSClient
from hmalib.common.models.signal import ThreatExchangeSignalMetadata

from mypy_boto3_dynamodb.service_resource import Table
from threatexchange.signal_type.pdq import PdqSignal
from hmalib.common.models.pipeline import MatchRecord
import typing as t
import time

from threatexchange.signal_type.index import IndexMatch, SignalTypeIndex
from threatexchange.signal_type.signal_base import SignalType

from hmalib import metrics
from hmalib.common.logging import get_logger
from hmalib.common.mappings import INDEX_MAPPING
from hmalib.common.messages.match import BankedSignal, MatchMessage
from hmalib.common.configs.fetcher import ThreatExchangeConfig


logger = get_logger(__name__)

PG_CONFIG_CACHE_TIME_SECONDS = 300


@functools.lru_cache(maxsize=128)
def _get_privacy_group_matcher_active(privacy_group_id: str, cache_buster) -> bool:
    config = ThreatExchangeConfig.get(privacy_group_id)
    if not config:
        logger.warning("Privacy group %s is not found!", privacy_group_id)
        return False

    logger.debug("matcher_active for %s is %s", privacy_group_id, config.matcher_active)
    return config.matcher_active


def get_privacy_group_matcher_active(privacy_group_id: str) -> bool:
    """
    Is this privacy group's matcher_active flag true? Entries in the internal
    cache are cleared every PG_CONFIG_CACHE_TIME_SECONDS seconds.

    Impl: the // is python's integer division operator. Threw me off. :)
    """
    return _get_privacy_group_matcher_active(
        privacy_group_id, time.time() // PG_CONFIG_CACHE_TIME_SECONDS
    )


class Matcher:
    """
    Match against any signal type defined on threatexchange and stored in s3.

    Once created, indexes used by this are cached on the index. Do not create
    multiple Matcher instances in the same python runtime for the same
    signal_type. This would take up more RAM than necessary.

    Indexes are pulled from S3 on first call for a signal_type.
    """

    def __init__(
        self,
        index_bucket_name: str,
        supported_signal_types: t.List[t.Type[SignalType]],
    ):
        self.index_bucket_name = index_bucket_name
        self.supported_signal_types = supported_signal_types
        self._cached_indexes: t.Dict[t.Type[SignalType], SignalTypeIndex] = {}

    def match(
        self, signal_type: t.Type[SignalType], signal_value: str
    ) -> t.List[IndexMatch]:
        """
        Returns MatchMessage which can be directly published to a queue.

        Note, this also filters out matches that are from datasets that have
        been de-activated.
        """
        index = self.get_index(signal_type)

        with metrics.timer(metrics.names.indexer.search_index):
            match_results: t.List[IndexMatch] = index.query(signal_value)

        if not match_results:
            # No matches found in the index
            return []

        return self.filter_match_results(match_results)

    def filter_match_results(self, results: t.List[IndexMatch]) -> t.List[IndexMatch]:
        """
        For ThreatExchange, use the privacy group's matcher_active flag to
        filter out match results that should not be returned.

        If implementing a matcher for something other than threat exchange,
        consider extending this class and implementing your own.
        """

        filtered_results = []
        for match in results:
            match.metadata["privacy_groups"] = list(
                filter(
                    lambda x: get_privacy_group_matcher_active(str(x)),
                    match.metadata.get("privacy_groups", []),
                )
            )

            if len(match.metadata["privacy_groups"]) != 0:
                filtered_results.append(match)

        return filtered_results

    def write_match_record_for_result(
        self,
        table: Table,
        signal_type: t.Type[SignalType],
        content_hash: str,
        content_id: str,
        match: IndexMatch,
    ):
        """
        Write a match record to dynamodb. The content_id is not important to the
        matcher. So, the calling lambda is expected to pass on the content_id
        for match record calls.
        """
        MatchRecord(
            content_id=content_id,
            signal_type=signal_type,
            content_hash=content_hash,
            updated_at=datetime.datetime.now(),
            signal_id=str(match.metadata["id"]),
            signal_source=match.metadata["source"],
            signal_hash=match.metadata["hash"],
            match_distance=int(match.distance),
        ).write_to_table(table)

    @classmethod
    def write_signal_if_not_found(
        cls,
        table: Table,
        signal_type: t.Type[SignalType],
        match: IndexMatch,
    ):
        """
        Write the signal to the datastore. Only signals that have matched are
        written to the DB. The fetcher takes care of updating the signal with
        opinions or updates from the source.

        TODO: Move this out of matchers.

        This is not matcher specific functionality. Signals could benefit from
        their own store. Perhaps the API could be useful when building local
        banks. Who knows! :)
        """
        for signal in cls.get_metadata_objects_from_match(signal_type, match):
            signal.write_to_table_if_not_found(table)

    @classmethod
    def get_metadata_objects_from_match(
        cls,
        signal_type: t.Type[SignalType],
        match: IndexMatch,
    ) -> t.List[t.Union[ThreatExchangeSignalMetadata]]:
        """
        See docstring of `write_signal_if_not_found` we will likely want to move
        this outside of Matcher. However while the MD5 expansion is still on going
        better to have it all in once place.
        Note: changes made here will have an effect on api.matches.get_match_for_hash
        """
        if (
            match.metadata["source"]
            != ThreatExchangeSignalMetadata.SIGNAL_SOURCE_SHORTCODE
        ):
            logger.warn(
                "Matched against signal that is not sourced from threatexchange. Not writing metadata object."
            )
            return []

        return [
            ThreatExchangeSignalMetadata(
                signal_id=str(match.metadata["id"]),
                privacy_group_id=privacy_group_id,
                updated_at=datetime.datetime.now(),
                signal_type=signal_type,
                signal_hash=match.metadata["hash"],
                tags=match.metadata["tags"].get(privacy_group_id, []),
            )
            for privacy_group_id in match.metadata.get("privacy_groups", [])
        ]

    def get_index(self, signal_type: t.Type[SignalType]) -> SignalTypeIndex:
        # If cached, return an index instance for the signal_type. If not, build
        # one, cache and return.
        if not signal_type in self._cached_indexes:
            index_cls = INDEX_MAPPING[signal_type]

            with metrics.timer(metrics.names.indexer.download_index):
                self._cached_indexes[signal_type] = index_cls.load(
                    bucket_name=self.index_bucket_name
                )

        return self._cached_indexes[signal_type]

    def publish_match_message(
        self,
        content_id: str,
        content_hash: str,
        matches: t.List[IndexMatch],
        sns_client: SNSClient,
        topic_arn: str,
    ):
        """
        Creates banked signal objects and publishes one message for a list of
        matches to SNS.
        """
        banked_signals = []

        for match in matches:
            for privacy_group_id in match.metadata.get("privacy_groups", []):
                banked_signal = BankedSignal(
                    str(match.metadata["id"]),
                    str(privacy_group_id),
                    str(match.metadata["source"]),
                )

                for tag in match.metadata["tags"].get(privacy_group_id, []):
                    banked_signal.add_classification(tag)

                banked_signals.append(banked_signal)

        match_message = MatchMessage(
            content_key=content_id,
            content_hash=content_hash,
            matching_banked_signals=banked_signals,
        )

        sns_client.publish(TopicArn=topic_arn, Message=match_message.to_aws_json())
