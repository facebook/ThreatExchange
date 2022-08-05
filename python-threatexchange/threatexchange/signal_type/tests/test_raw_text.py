# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

from threatexchange.signal_type.tests.signal_type_test_helper import MatchesStrAutoTest

from threatexchange.signal_type.raw_text import RawTextSignal


class TestRawTextSignal(MatchesStrAutoTest):

    TYPE = RawTextSignal

    def get_validate_hash_cases(self):
        return [
            ("a", "a"),
            ("a ", "a"),
        ]

    def get_compare_hash_cases(self):
        return []

    def get_matches_str_cases(self):
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
