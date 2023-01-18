# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Implements a unified matcher class. The unified matcher is capable of matching
against any index defined in python-threatexchange.
"""

import datetime

from mypy_boto3_sns.client import SNSClient
from mypy_boto3_dynamodb.service_resource import Table
import typing as t

from threatexchange.interface_validation import FunctionalityMapping
from threatexchange.signal_type.index import IndexMatch, SignalTypeIndex
from threatexchange.signal_type.signal_base import SignalType

from hmalib.common.models.bank import BanksTable
from hmalib.common.models.pipeline import MatchRecord
from hmalib import metrics
from hmalib.common.logging import get_logger
from hmalib.common.messages.match import BankedSignal, MatchMessage
from hmalib.indexers.index_store import S3PickledIndexStore
from hmalib.common.models.signal import ThreatExchangeSignalMetadata
from hmalib.indexers.metadata import (
    BANKS_SOURCE_SHORT_CODE,
    THREAT_EXCHANGE_SOURCE_SHORT_CODE,
    BaseIndexMetadata,
    ThreatExchangeIndicatorIndexMetadata,
    BankedSignalIndexMetadata,
)
from hmalib.matchers.filters import (
    BankActiveFilter,
    BaseMatchFilter,
    ThreatExchangePdqMatchDistanceFilter,
    ThreatExchangePrivacyGroupMatcherActiveFilter,
    get_max_threshold_of_active_privacy_groups_for_signal_type,
)


logger = get_logger(__name__)


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
        banks_table: BanksTable,
    ):
        self.index_store = S3PickledIndexStore(index_bucket_name)
        self.supported_signal_types = supported_signal_types
        self._cached_indexes: t.Dict[t.Type[SignalType], SignalTypeIndex] = {}
        self.banks_table = banks_table

        self.match_filters: t.Sequence[BaseMatchFilter] = [
            ThreatExchangePrivacyGroupMatcherActiveFilter(),
            ThreatExchangePdqMatchDistanceFilter(),
            BankActiveFilter(banks_table=banks_table),
        ]

    def match(
        self, signal_type: t.Type[SignalType], signal_value: str
    ) -> t.List[IndexMatch[t.List[BaseIndexMetadata]]]:
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

        return self.filter_match_results(match_results, signal_type)

    def filter_match_results(
        self, results: t.List[IndexMatch], signal_type: t.Type[SignalType]
    ) -> t.List[IndexMatch]:
        """
        For ThreatExchange, use the privacy group's matcher_active flag to
        filter out match results that should not be returned.

        If implementing a matcher for something other than threat exchange,
        consider extending this class and implementing your own.
        """

        # results is a list of match object references that live in any index
        # this method should not edit those objects directly as they could effect
        # subsequent calls made while the index is still in memory
        matches = results.copy()

        for match_filter in self.match_filters:
            matches = match_filter.filter_matches(matches, signal_type)

        return matches

    def write_match_record_for_result(
        self,
        table: Table,
        signal_type: t.Type[SignalType],
        content_hash: str,
        content_id: str,
        match: IndexMatch[t.List[BaseIndexMetadata]],
    ):
        """
        Write a match record to dynamodb. The content_id is not important to the
        matcher. So, the calling lambda is expected to pass on the content_id
        for match record calls.
        """
        for metadata_obj in match.metadata:
            match_record_attributes = {
                "content_id": content_id,
                "signal_type": signal_type,
                "content_hash": content_hash,
                "updated_at": datetime.datetime.now(),
                "signal_source": metadata_obj.get_source(),
                "match_distance": int(match.similarity_info.distance),
            }

            if metadata_obj.get_source() == THREAT_EXCHANGE_SOURCE_SHORT_CODE:
                metadata_obj = t.cast(
                    ThreatExchangeIndicatorIndexMetadata, metadata_obj
                )
                match_record_attributes.update(
                    signal_id=metadata_obj.indicator_id,
                    signal_hash=metadata_obj.signal_value,
                )

            elif metadata_obj.get_source() == BANKS_SOURCE_SHORT_CODE:
                metadata_obj = t.cast(BankedSignalIndexMetadata, metadata_obj)
                match_record_attributes.update(
                    signal_id=metadata_obj.signal_id,
                    signal_hash=metadata_obj.signal_value,
                )

            MatchRecord(**match_record_attributes).write_to_table(table)

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
        for signal in cls.get_te_metadata_objects_from_match(signal_type, match):
            if hasattr(signal, "write_to_table_if_not_found"):
                # only ThreatExchangeSignalMetadata has this method.
                # mypy not smart enough to auto cast.
                signal.write_to_table_if_not_found(table)  # type: ignore

    @classmethod
    def get_te_metadata_objects_from_match(
        cls,
        signal_type: t.Type[SignalType],
        match: IndexMatch[t.List[BaseIndexMetadata]],
    ) -> t.List[ThreatExchangeSignalMetadata]:
        """
        See docstring of `write_signal_if_not_found` we will likely want to move
        this outside of Matcher. However while the MD5 expansion is still on going
        better to have it all in once place.
        Note: changes made here will have an effect on api.matches.get_match_for_hash
        """
        metadata_objects = []
        for metadata_obj in match.metadata:
            if metadata_obj.get_source() == THREAT_EXCHANGE_SOURCE_SHORT_CODE:
                metadata_obj = t.cast(
                    ThreatExchangeIndicatorIndexMetadata, metadata_obj
                )
                metadata_objects.append(
                    ThreatExchangeSignalMetadata(
                        signal_id=str(metadata_obj.indicator_id),
                        privacy_group_id=metadata_obj.privacy_group,
                        updated_at=datetime.datetime.now(),
                        signal_type=signal_type,
                        signal_hash=metadata_obj.signal_value,
                        tags=list(metadata_obj.tags),
                    )
                )
        return metadata_objects

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
                self._cached_indexes[signal_type] = self.index_store.load(index_cls)

        return self._cached_indexes[signal_type]

    @classmethod
    def _get_index_for_signal_type_matching(
        cls, signal_type: t.Type[SignalType], max_custom_threshold: int
    ):
        # TODO: Figure out how to switch index type when max_custom_threshold
        # changes.
        index_type = signal_type.get_index_cls()
        return index_type

    def publish_match_message(
        self,
        content_id: str,
        content_hash: str,
        matches: t.List[IndexMatch[t.List[BaseIndexMetadata]]],
        sns_client: SNSClient,
        topic_arn: str,
    ):
        """
        Creates banked signal objects and publishes one message for a list of
        matches to SNS.
        """
        banked_signals = []

        for match in matches:
            for metadata_obj in match.metadata:
                if metadata_obj.get_source() == THREAT_EXCHANGE_SOURCE_SHORT_CODE:
                    metadata_obj = t.cast(
                        ThreatExchangeIndicatorIndexMetadata, metadata_obj
                    )
                    banked_signal = BankedSignal(
                        str(metadata_obj.indicator_id),
                        str(metadata_obj.privacy_group),
                        str(metadata_obj.get_source()),
                    )
                    for tag in metadata_obj.tags:
                        banked_signal.add_classification(tag)

                    banked_signals.append(banked_signal)
                elif metadata_obj.get_source() == BANKS_SOURCE_SHORT_CODE:
                    metadata_obj = t.cast(BankedSignalIndexMetadata, metadata_obj)
                    bank_member = self.banks_table.get_bank_member(
                        bank_member_id=metadata_obj.bank_member_id
                    )

                    banked_signal = BankedSignal(
                        metadata_obj.bank_member_id,
                        bank_member.bank_id,
                        metadata_obj.get_source(),
                    )

                    # TODO: This would do good with caching.
                    bank = self.banks_table.get_bank(bank_id=bank_member.bank_id)
                    for tag in set.union(bank_member.bank_member_tags, bank.bank_tags):
                        banked_signal.add_classification(tag)

                    banked_signals.append(banked_signal)

        match_message = MatchMessage(
            content_key=content_id,
            content_hash=content_hash,
            matching_banked_signals=banked_signals,
        )

        sns_client.publish(TopicArn=topic_arn, Message=match_message.to_aws_json())
