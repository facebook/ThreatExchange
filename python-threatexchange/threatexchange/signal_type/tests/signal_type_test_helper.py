# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import pytest
import typing as t

from threatexchange.signal_type.signal_base import (
    FileHasher,
    MatchesStr,
    SignalType,
    TextHasher,
)


class SignalTypeHashTest:
    """
    Helpers to help you quickly test common functionality

    Most functions are designed to be used to be used in a provider fasion
    to rapidly make simple tests.
    """

    TYPE: t.ClassVar[t.Type[SignalType]]

    def assert_signal_str_valid(
        self, s: str, expected: t.Optional[str] = None, *, valid: bool = True
    ):
        if not valid:
            self.assert_signal_str_invalid(s)
            return
        expected = s if expected is None else expected
        validated = self.TYPE.validate_signal_str(s)
        assert expected == validated

    def assert_signal_str_invalid(
        self, s: str, expected_exception=Exception, *args, **kwargs
    ) -> None:
        with pytest.raises(expected_exception, *args, **kwargs):
            self.TYPE.validate_signal_str(s)


THashValidateCase = t.Union[str, t.Tuple[str, t.Union[None, str, t.Type[Exception]]]]
THashCompareCase = t.Union[
    t.Tuple[str, str], t.Tuple[str, str, bool], t.Tuple[str, str, bool, t.Any]
]


class SignalTypeAutoTest(SignalTypeHashTest):
    """
    A helper to automatically generate a bunch of simple tests for a SignalType.

    If you create a test class that extends this one, it will automatically create
    test cases, which you can provide test data by implementing the *_cases().

    check out test_raw_text.py in this directory for a simple example

    This is probably not the cleanest way you could have done this, but it's
    probably better than nothing.
    """

    def test_get_name(self):
        assert self.TYPE.get_name()
        # Could also test for collisions, but ¯\_(ツ)_/¯

    def test_examples(self):
        examples = self.TYPE.get_examples()
        # It's possible that there some SignalTypes where this doesn't make
        # sense, in which case you can override this test to just always pass
        assert examples, f"Add some examples to {self.TYPE.__name__}.get_examples()"
        for example in examples:
            self.assert_signal_str_valid(example)
            if issubclass(self.TYPE, FileHasher):
                assert self.TYPE.compare_hash(
                    example, example
                ).match, f"Case: {example}"

    def get_validate_hash_cases(self) -> t.Iterable[THashValidateCase]:
        raise NotImplementedError

    def test_validate_hash(self):
        for t in self.get_validate_hash_cases():
            if isinstance(t, str):
                t = (t, None)
            s, expected = t
            if isinstance(expected, type):  # Exception
                self.assert_signal_str_invalid(s, expected)
            else:
                self.assert_signal_str_valid(s, expected)

    def get_compare_hash_cases(self) -> t.Iterable[THashValidateCase]:
        raise NotImplementedError

    def test_compare_hash(self):
        for t in self.get_compare_hash_cases():
            assert issubclass(self.TYPE, FileHasher)  # For typing
            a, b = t[:2]
            expect_match = t[2] if len(t) > 2 else True

            result = self.TYPE.compare_hash(a, b)
            assert result.match == expect_match, f"Case: {t}"
            if len(t) > 3:
                assert result.distance == t[3]


class TextHasherAutoTest(SignalTypeAutoTest):
    """
    Auto-testing, but with TextHasher classes
    """

    def get_hashes_from_str_cases(self) -> t.Iterable[t.Tuple[str, str]]:
        raise NotImplementedError

    def test_hash_from_str(self):
        assert issubclass(self.TYPE, TextHasher)  # For typing
        for s, hashed in self.get_hashes_from_str_cases():
            assert self.TYPE.hash_from_str(s) == hashed, f"Case: {(s, hashed)}"


TMatchesStrCase = t.Union[
    t.Tuple[str, str], t.Tuple[str, str, bool], t.Tuple[str, str, bool, t.Any]
]


class MatchesStrAutoTest(SignalTypeAutoTest):
    """
    Auto-testing, but with MatchesStr classes
    """

    def get_matches_str_cases(self) -> t.Iterable[TMatchesStrCase]:
        raise NotImplementedError

    def test_matches_str(self):
        for t in self.get_matches_str_cases():
            signal, haystack = t[:2]
            expect_match = t[2] if len(t) > 2 else True

            result = self.TYPE.matches_str(signal, haystack)
            assert result.match == expect_match, f"Case: {t}"
            if len(t) > 3:
                assert result.distance.distance == t[3], f"Case: {t}"
