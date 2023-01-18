# Copyright (c) Meta Platforms, Inc. and affiliates.

import unittest

from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.pdq import PdqSignal
from threatexchange.signal_type.index import IndexMatch
from threatexchange.content_type.photo import PhotoContent

from hmalib.common.config import HMAConfig, create_config
from hmalib.common.configs.fetcher import (
    AdditionalMatchSettingsConfig,
    ThreatExchangeConfig,
)
from hmalib.common.models.bank import BanksTable
from hmalib.indexers.metadata import (
    ThreatExchangeIndicatorIndexMetadata,
    BankedSignalIndexMetadata,
)
from hmalib.matchers.matchers_base import Matcher

from hmalib.common.models.tests.test_signal_uniqueness import BanksTableTestBase
from hmalib.common.tests import config_test
from hmalib.common.tests.mapping_common import get_default_signal_type_mapping


class MatchFiltersTestCase(BanksTableTestBase, unittest.TestCase):
    # NOTE: Table is defined in base class BanksTableTestBase

    def _create_banks(self):
        self.table_manager = BanksTable(
            self.get_table(), get_default_signal_type_mapping()
        )

        self.active_bank = self.table_manager.create_bank("TEST_BANK", "Is Active")
        self.active_bank_member = self.table_manager.add_bank_member(
            bank_id=self.active_bank.bank_id,
            content_type=PhotoContent,
            raw_content=None,
            storage_bucket=None,
            storage_key=None,
            notes=None,
        )
        self.table_manager.update_bank(
            bank_id=self.active_bank.bank_id,
            bank_name=self.active_bank.bank_name,
            bank_description=self.active_bank.bank_description,
            is_active=True,
        )

        self.inactive_bank = self.table_manager.create_bank(
            "TEST_BANK_2", "Is Inactive"
        )
        self.table_manager.update_bank(
            bank_id=self.inactive_bank.bank_id,
            bank_name=self.inactive_bank.bank_name,
            bank_description=self.inactive_bank.bank_description,
            is_active=False,
        )
        self.inactive_bank_member = self.table_manager.add_bank_member(
            bank_id=self.inactive_bank.bank_id,
            content_type=PhotoContent,
            raw_content=None,
            storage_bucket=None,
            storage_key=None,
            notes=None,
        )

    def _create_privacy_groups(self):
        # Since we already have a mock_dynamodb2 courtesy BanksTableTestBase,
        # re-use it for initing configs. Requires some clever hot-wiring.
        config_test_mock = config_test.ConfigTest()
        config_test_mock.mock_dynamodb2 = self.__class__.mock_dynamodb2
        config_test_mock.create_mocked_table()
        HMAConfig.initialize(config_test_mock.TABLE_NAME)
        # Hot wiring ends...

        self.active_pg = ThreatExchangeConfig(
            "ACTIVE_PG", True, "", True, True, True, "ACTIVE_PG"
        )
        create_config(self.active_pg)

        # Active PG has a distance threshold of 31.
        create_config(AdditionalMatchSettingsConfig("ACTIVE_PG", 31))

        self.inactive_pg = ThreatExchangeConfig(
            "INACTIVE_PG", True, "", True, True, False, "INACTIVE_PG"
        )
        create_config(self.inactive_pg)

    def _init_data_if_required(self):
        self._create_banks()
        self._create_privacy_groups()

    def _active_pg_match(self):
        return IndexMatch(
            0,
            [
                ThreatExchangeIndicatorIndexMetadata(
                    "indicator_id",
                    "hash_value",
                    self.active_pg.privacy_group_id,
                )
            ],
        )

    def _inactive_pg_match(self):
        return IndexMatch(
            0,
            [
                ThreatExchangeIndicatorIndexMetadata(
                    "indicator_id",
                    "hash_value",
                    self.inactive_pg.privacy_group_id,
                )
            ],
        )

    def _active_bank_match(self):
        return IndexMatch(
            0,
            [
                BankedSignalIndexMetadata(
                    "signal", "signal_value", self.active_bank_member.bank_member_id
                )
            ],
        )

    def _inactive_bank_match(self):
        return IndexMatch(
            0,
            [
                BankedSignalIndexMetadata(
                    "signal", "signal_value", self.inactive_bank_member.bank_member_id
                )
            ],
        )

    def test_matcher_filters_out_inactive_pg(self):
        with self.fresh_dynamodb():
            self._init_data_if_required()

            matcher = Matcher("", [PdqSignal, VideoMD5Signal], self.table_manager)
            filtered_matches = matcher.filter_match_results(
                [self._active_pg_match(), self._inactive_pg_match()],
                PdqSignal,
            )

            self.assertEqual(
                len(filtered_matches), 1, "Failed to filter out inactive pg match"
            )
            self.assertEqual(
                filtered_matches[0].metadata[0].privacy_group,
                self.active_pg.privacy_group_id,
                "The filtered privacy group id is wrong. It should be the active pg's id.",
            )

    def test_matcher_filters_out_based_on_distance(self):
        with self.fresh_dynamodb():
            self._init_data_if_required()

            match_1 = self._active_pg_match()
            match_2 = self._active_pg_match()

            match_2.similarity_info = 100

            matcher = Matcher("", [PdqSignal, VideoMD5Signal], self.table_manager)
            filtered_matches = matcher.filter_match_results(
                [match_1, match_2], PdqSignal
            )

            self.assertEqual(
                len(filtered_matches),
                1,
                "Failed to filter out match with distance > threshold",
            )

            self.assertEqual(
                filtered_matches[0].similarity_info,
                0,
                "Filtered out the wrong match. Match with distance = 100 should be filtered out.",
            )

    def test_matcher_filters_out_based_on_bank_active(self):
        with self.fresh_dynamodb():
            self._init_data_if_required()

            matcher = Matcher("", [PdqSignal, VideoMD5Signal], self.table_manager)
            filtered_matches = matcher.filter_match_results(
                [self._active_bank_match(), self._inactive_bank_match()],
                PdqSignal,
            )

            self.assertEqual(
                len(filtered_matches), 1, "Failed to filter out inactive bank's match"
            )
            self.assertEqual(
                filtered_matches[0].metadata[0].bank_member_id,
                self.active_bank_member.bank_member_id,
                "The filtered bank_member id is wrong. It should be the active bank's bank_member's id.",
            )
