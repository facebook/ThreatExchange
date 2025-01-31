# Copyright (c) Meta Platforms, Inc. and affiliates.

import pytest
from threatexchange.signal_type.raw_text import RawTextSignal
from threatexchange.signal_type.tests.signal_type_test_helper import MatchesStrAutoTest


class TestRawTextSignal(MatchesStrAutoTest):
    TYPE = RawTextSignal

    @pytest.mark.parametrize(
        "input_val, expected_hash",
        [
            ("a", "a"),
            ("a ", "a"),
        ],
    )
    def test_validate_hash(self, input_val, expected_hash):
        assert self.TYPE.validate_hash(input_val) == expected_hash, (
            f"Expected {expected_hash} for input {input_val}, but got "
            f"{self.TYPE.validate_hash(input_val)}"
        )

    @pytest.mark.parametrize("input_val, expected_result", [])
    def test_compare_hash(self, input_val, expected_result):
        assert self.TYPE.compare_hash(input_val) == expected_result, (
            f"Expected {expected_result} for input {input_val}, but got "
            f"{self.TYPE.compare_hash(input_val)}"
        )

    @pytest.mark.parametrize(
        "input_str, match_str, expected_match, threshold",
        [
            ("", "", True, 0),  # Empty strings match
            ("a", "a", True, 0),  # Identical single-character match
            ("a", "b", False, 1),  # Single-character mismatch
            ("aaaaaaaaaa", "a", False, 9),  # Longer string doesn't match shorter
            ("a", "aaaaaaaaa", False, 8),  # Shorter string doesn't match longer
            ("a a a a a a a a a", "aaaaaaaaa", True, 0),  # Normalization removes spaces
            ("a" * 19, "a" * 18 + "b", False, 1),  # Fails threshold 95%
            ("a" * 20, "a" * 19 + "b", True, 1),  # Meets threshold with 20 chars
        ],
    )
    def test_matches_str(self, input_str, match_str, expected_match, threshold):
        result = self.TYPE.matches_str(input_str, match_str, threshold)
        assert result == expected_match, (
            f"Expected {expected_match} for input ({input_str}, {match_str}) with "
            f"threshold {threshold}, but got {result}"
        )
