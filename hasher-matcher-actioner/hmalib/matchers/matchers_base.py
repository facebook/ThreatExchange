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
from hmalib.common.configs.fetcher import (
    ThreatExchangeConfig,
    AdditionalMatchSettingsConfig,
)


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


@functools.lru_cache(maxsize=None)
def _get_all_matcher_active_privacy_groups(cache_buster) -> t.List[str]:
    configs = ThreatExchangeConfig.get_all()
    return list(
        map(
            lambda c: c.name,
            filter(
                lambda c: c.matcher_active,
                configs,
            ),
        )
    )


@functools.lru_cache(maxsize=None)
def _get_max_pdq_threshold_for_active_matcher_privacy_groups(
    cache_buster,
) -> int:
    active_pg_names = _get_all_matcher_active_privacy_groups(cache_buster)
    if not active_pg_names:
        return 0
    active_pdq_thresholds = [
        config.pdq_match_threshold
        for config in AdditionalMatchSettingsConfig.get_all()
        if config.name in active_pg_names
    ]
    if active_pdq_thresholds:
        return max(active_pdq_thresholds)
    # no custom threshold set for active privacy_groups
    return 0


def get_max_threshold_of_active_privacy_groups_for_signal_type(
    signal_type: t.Type[SignalType],
) -> int:
    if signal_type == PdqSignal:
        return _get_max_pdq_threshold_for_active_matcher_privacy_groups(
            time.time() // PG_CONFIG_CACHE_TIME_SECONDS
        )
    else:
        return 0


@functools.lru_cache(maxsize=128)
def _get_optional_privacy_group_matcher_pdq_theshold(
    privacy_group_id: str, cache_buster
) -> t.Optional[int]:
    config = AdditionalMatchSettingsConfig.get(privacy_group_id)
    if not config:
        logger.debug(
            "Privacy group %s does not have custom pdq_match_threshold.",
            privacy_group_id,
        )
        return None

    logger.debug(
        "pdq_match_threshold for %s is %s", privacy_group_id, config.pdq_match_threshold
    )
    return config.pdq_match_threshold


def get_optional_privacy_group_matcher_pdq_theshold(
    privacy_group_id: str,
) -> t.Optional[int]:
    """
    Does this privacy group's have a custom pdq threshold; if so what is it?
    Entries in the internal cache are cleared
    every PG_CONFIG_CACHE_TIME_SECONDS seconds.

    Impl: the // is python's integer division operator. Threw me off. :)
    """
    return _get_optional_privacy_group_matcher_pdq_theshold(
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

        filtered_results_based_on_active = []
        for match in results:
            match.metadata["privacy_groups"] = list(
                filter(
                    lambda x: get_privacy_group_matcher_active(str(x)),
                    match.metadata.get("privacy_groups", []),
                )
            )

            if len(match.metadata["privacy_groups"]) != 0:
                filtered_results_based_on_active.append(match)

        # Also check and see if there is a custom threshold filter
        filtered_results_based_on_threshold = []
        for match in filtered_results_based_on_active:
            filtered_privacy_groups = []
            for privacy_group in match.metadata.get("privacy_groups", []):
                if threshold := get_optional_privacy_group_matcher_pdq_theshold(
                    str(privacy_group)
                ):
                    if match.distance >= threshold:
                        logger.debug(
                            "Match was found at %s distance but exceeds custom theshold of %s for pg, %s",
                            match.distance,
                            threshold,
                            privacy_group,
                        )
                    else:
                        filtered_privacy_groups.append(privacy_group)
                else:
                    # no custom threshold found
                    filtered_privacy_groups.append(privacy_group)
            match.metadata["privacy_groups"] = filtered_privacy_groups

            if len(match.metadata["privacy_groups"]) != 0:
                filtered_results_based_on_threshold.append(match)

        return filtered_results_based_on_threshold

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
        """
        If cached, return an index instance for the signal_type. If not, build
        one, cache and return.
        """

        max_custom_threshold = (
            get_max_threshold_of_active_privacy_groups_for_signal_type(signal_type)
        )
        index_cls = self._get_index_for_signal_type_matching(
            signal_type, max_custom_threshold
        )

        # Check for signal_type in cache AND confirm said index class type is
        # still correct for the given [optional] max_custom_threshold
        if not signal_type in self._cached_indexes or not isinstance(
            self._cached_indexes[signal_type], index_cls
        ):
            with metrics.timer(metrics.names.indexer.download_index):
                self._cached_indexes[signal_type] = index_cls.load(
                    bucket_name=self.index_bucket_name
                )

        return self._cached_indexes[signal_type]

    @classmethod
    def _get_index_for_signal_type_matching(
        cls, signal_type: t.Type[SignalType], max_custom_threshold: int = 0
    ):
        indexes = INDEX_MAPPING[signal_type]
        # disallow empty list
        assert indexes
        if len(indexes) == 1:
            # if we only have one option just return
            return indexes[0]

        indexes.sort(key=lambda i: i.get_index_max_distance())

        for index_cls in indexes:
            if max_custom_threshold <= index_cls.get_index_max_distance():
                return index_cls

        # if we don't have an index that supports max threshold
        # just return the one if the highest possible max distance
        return indexes[-1]

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
