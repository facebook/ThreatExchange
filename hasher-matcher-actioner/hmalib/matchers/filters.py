# Copyright (c) Meta Platforms, Inc. and affiliates.

from sys import maxsize
import typing as t
import time
import functools
import methodtools

from threatexchange.signal_type.index import IndexMatch
from threatexchange.signal_type.pdq import PdqSignal
from threatexchange.signal_type.signal_base import SignalType

from hmalib.indexers.metadata import (
    BANKS_SOURCE_SHORT_CODE,
    THREAT_EXCHANGE_SOURCE_SHORT_CODE,
    BankedSignalIndexMetadata,
    BaseIndexMetadata,
    ThreatExchangeIndicatorIndexMetadata,
)
from hmalib.common.logging import get_logger
from hmalib.common.configs.fetcher import (
    ThreatExchangeConfig,
    AdditionalMatchSettingsConfig,
)
from hmalib.common.models.bank import BankMember, BanksTable


logger = get_logger(__name__)


PG_CONFIG_CACHE_TIME_SECONDS = 300
BANK_CACHE_TIME_SECONDS = 300
BANK_CACHE_SIZE = 200


class BaseMatchFilter:
    """
    All classes implementing their own match filter logic should implement this
    interface.

    Implementing classes are called by the matcher and then the `filter_matches`
    method is called.

    A sub class can either (re)define `filter_matches` or just
    `should_process_metadata_obj` (RECOMMENDED). The benefit of defining just
    `should_process_metadata_obj` is that the logging is centrally handled and we
    reduce *some* redundancies.

    If you need more control, or there are benefits to handling all matches
    together, (re)define `filter_matches`.
    """

    def filter_matches(
        self,
        matches: t.List[IndexMatch[BaseIndexMetadata]],
        index_signal_type: t.Type[SignalType],
    ) -> t.List[IndexMatch]:
        """
        The only publicly used method of this interface. Given a list of index
        matches, filter some out.

        Note matches is a list of IndexMatches and IndexMatches.metadata is a
        list of objects subclassing BaseIndexMetadata.

        Typically, you'd implement should_process_metadata_obj which would have
        an opinion on a specific match_metadata.

        Let's take an example. Hash H1 is present in threatexchange and in a
        local bank. So, matching a close hash H2 results in an IndexMatch object
        with two metadata objects. You'd want the filters to individually
        inspect the threatexchange and the local bank metadata.
        """

        results = []
        for match in matches:
            metadata_results = []
            for metadata_obj in match.metadata:
                filter_one_result = self.should_process_metadata_obj(
                    metadata_obj, index_signal_type, match.similarity_info
                )
                if type(filter_one_result) != bool or filter_one_result:
                    # If should_process_metadata_obj returned a non boolean
                    # response, we don't want to filter out based on that.
                    # Default to processing that metadata.
                    metadata_results.append(metadata_obj)
                else:
                    logger.info(
                        "Filtering out metadata object {%s} because MatchFilter%s said so.",
                        repr(metadata_obj),
                        str(self.__class__),
                    )

            match.metadata = metadata_results

            if len(match.metadata) != 0:
                results.append(match)

        return results

    def should_process_metadata_obj(
        self,
        match: BaseIndexMetadata,
        index_signal_type: t.Type[SignalType],
        match_distance: int,
    ) -> bool:
        """
        Should one index_match object be filtered.

        @return True to process this match or to not have an opinion.
        @return False to filter out and NOT process this match.

        Non boolean results are ignored so they default to True.
        """
        raise NotImplementedError


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
def _get_privacy_group_matcher_pdq_threshold(
    privacy_group_id: str, cache_buster
) -> int:
    config = AdditionalMatchSettingsConfig.get(privacy_group_id)
    if not config:
        logger.debug(
            "Privacy group %s does not have custom pdq_match_threshold. Using default defined in PDQ_CONFIDENT_MATCH_THRESHOLD",
            privacy_group_id,
        )
        return PdqSignal.PDQ_CONFIDENT_MATCH_THRESHOLD

    logger.debug(
        "pdq_match_threshold for %s is %s", privacy_group_id, config.pdq_match_threshold
    )
    return config.pdq_match_threshold


def get_privacy_group_matcher_pdq_threshold(
    privacy_group_id: str,
) -> int:
    """
    Does this privacy group's have a custom pdq threshold; if so what is it?
    otherwise return the default PDQ_CONFIDENT_MATCH_THRESHOLD.

    Entries in the internal cache are cleared
    every PG_CONFIG_CACHE_TIME_SECONDS seconds.

    ToDo this should be refactored into a signal angostic interface eventaully
        especially before we have another similarity based signal type in HMA

    Impl: the // is python's integer division operator. Threw me off. :)
    """
    return _get_privacy_group_matcher_pdq_threshold(
        privacy_group_id, time.time() // PG_CONFIG_CACHE_TIME_SECONDS
    )


class ThreatExchangePrivacyGroupMatcherActiveFilter(BaseMatchFilter):
    """
    Filter out matches against privacy groups which are not active at the
    moment.
    """

    def should_process_metadata_obj(
        self,
        match: BaseIndexMetadata,
        index_signal_type: t.Type[SignalType],
        match_distance: int,
    ) -> bool:
        if match.get_source() != THREAT_EXCHANGE_SOURCE_SHORT_CODE:
            # Do not have an opinion on matches outside threatexchange
            return True

        te_match = t.cast(ThreatExchangeIndicatorIndexMetadata, match)
        return get_privacy_group_matcher_active(te_match.privacy_group)


class ThreatExchangePdqMatchDistanceFilter(BaseMatchFilter):
    """
    Filter out matches where the match distance is > the threshold set for that
    privacy group.
    """

    def should_process_metadata_obj(
        self,
        match: BaseIndexMetadata,
        index_signal_type: t.Type[SignalType],
        match_distance: int,
    ) -> bool:
        if match.get_source() != THREAT_EXCHANGE_SOURCE_SHORT_CODE:
            # Do not have an opinion on matches outside threatexchange
            return True

        if index_signal_type != PdqSignal:
            # Do not have an opinion on matches that are not pdq
            return True

        pg_matcher_threshold = get_privacy_group_matcher_pdq_threshold(
            str(t.cast(ThreatExchangeIndicatorIndexMetadata, match).privacy_group)
        )
        return match_distance <= pg_matcher_threshold


class BankActiveFilter(BaseMatchFilter):
    """
    Filter out matches from banks where the is_active flag is False.
    """

    def __init__(self, banks_table: BanksTable):
        self.banks_table = banks_table

    def should_process_metadata_obj(
        self,
        match: BaseIndexMetadata,
        index_signal_type: t.Type[SignalType],
        match_distance: int,
    ) -> bool:
        if match.get_source() != BANKS_SOURCE_SHORT_CODE:
            # Do not have an opinion on matches that are not from banks.
            return True

        bank_match = t.cast(BankedSignalIndexMetadata, match)
        return self.get_bank_active(bank_match.bank_member_id)

    def get_bank_active(self, bank_member_id: str) -> bool:
        """
        Is the bank active? Use the bank_member_id to get an answer. Note
        bank_id -> active is cached, but bank_member_id -> bank_id is not.
        """
        member = self.get_bank_member_internal(
            bank_member_id, time.time() // BANK_CACHE_TIME_SECONDS
        )
        return self.get_bank_active_internal(
            member.bank_id, time.time() // BANK_CACHE_TIME_SECONDS
        )

    @methodtools.lru_cache(maxsize=BANK_CACHE_SIZE)
    def get_bank_active_internal(self, bank_id: str, cache_buster) -> bool:
        """
        Retrieves is_active from the banks table. Use a time.time() // CACHE_TIME
        style value for `cache_buster` to add a sort of TTL.
        """
        return self.banks_table.get_bank(bank_id=bank_id).is_active

    @methodtools.lru_cache(maxsize=BANK_CACHE_SIZE)
    def get_bank_member_internal(self, bank_member_id: str, cache_buster) -> BankMember:
        """
        Retrieves a bank_member from the banks table. Use a time.time() //
        CACHE_TIME style value for `cache_buster` to add a sort of TTL.
        """
        return self.banks_table.get_bank_member(bank_member_id=bank_member_id)
