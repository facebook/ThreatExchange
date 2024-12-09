# Copyright (c) Meta Platforms, Inc. and affiliates.

import pytest
from threatexchange.signal_type.raw_text import RawTextSignal
from threatexchange.signal_type.tests.signal_type_test_helper import MatchesStrAutoTest

from threatexchange.signal_type.raw_text import RawTextSignal


class TestRawTextSignal(MatchesStrAutoTest):
    TYPE = RawTextSignal

    @pytest.fixture
    def validate_hash_cases(self):
        return [
            ("a", "a"),
            ("a ", "a"),
        ]

    @pytest.fixture
    def compare_hash_cases(self):
        return []

    @pytest.fixture
    def matches_str_cases(self):
        return [
            ("", ""),
            ("a", "a"),
            ("a", "b", False, 1),
            ("aaaaaaaaaa", "a", False, 9),
            ("a", "aaaaaaaaa", False, 8),
            # Normalization removes spaces
            ("a a a a a a a a a", "aaaaaaaaa", True, 0),
            # Default threshold is 95%
            ("a" * 19, "a" * 18 + "b", False, 1),
            ("a" * 20, "a" * 19 + "b", True, 1),
        ]

    def test_validate_hash(self, validate_hash_cases):
        for case in validate_hash_cases:
            input_val, expected_hash = case
            assert self.TYPE.validate_hash(input_val) == expected_hash

    def test_compare_hash(self, compare_hash_cases):
        for case in compare_hash_cases:
            input_val, expected_result = case
            assert self.TYPE.compare_hash(input_val) == expected_result

    def test_matches_str(self, matches_str_cases):
        for case in matches_str_cases:
            input_str, match_str, expected_match, threshold = case
            assert (
                self.TYPE.matches_str(input_str, match_str, threshold) == expected_match
            )
