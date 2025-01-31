# Copyright (c) Meta Platforms, Inc. and affiliates.

import pytest
from threatexchange.signal_type.raw_text import RawTextSignal
from threatexchange.signal_type.tests.signal_type_test_helper import (
    MatchesStrAutoTest,
    THashValidateCase,
    TMatchesStrCase,
)
import typing as t


class TestRawTextSignal(MatchesStrAutoTest):
    TYPE = RawTextSignal

    def get_validate_hash_cases(self) -> t.Iterable[THashValidateCase]:
        return [
            ("a", "a"),  # Normal case
            ("a ", "a"),  # Whitespace is trimmed
        ]

    @pytest.mark.skip(reason="RawTextSignal is not a FileHasher, compare_hash is not supported")
    def test_compare_hash(self) -> None:
        pass

    def get_matches_str_cases(self) -> t.Iterable[TMatchesStrCase]:
        return [
            ("", "", True, 0),  # Empty strings match
            ("a", "a", True, 0),  # Identical single-character match
            ("a", "b", False, 1),  # Single-character mismatch
            ("aaaaaaaaaa", "a", False, 9),  # Longer string doesn't match shorter
            ("a", "aaaaaaaaa", False, 8),  # Shorter string doesn't match longer
            ("a a a a a a a a a", "aaaaaaaaa", True, 0),  # Normalization removes spaces
            ("a" * 19, "a" * 18 + "b", False, 1),  # Fails threshold 95%
            ("a" * 20, "a" * 19 + "b", True, 1),  # Meets threshold with 20 chars
        ]

    @pytest.mark.parametrize(
        "input_val, expected_str",
        [
            ("a", "a"),
            ("a ", "a"),
        ],
    )
    def test_validate_signal_str(self, input_val: str, expected_str: str) -> None:
        validated = self.TYPE.validate_signal_str(input_val)
        assert validated == expected_str, (
            f"Expected {expected_str} for input {input_val}, but got " f"{validated}"
        )
