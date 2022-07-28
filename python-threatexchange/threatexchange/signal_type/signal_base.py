#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Core abstractions for signal types.
"""

import pathlib
import typing as t

from threatexchange import common
from threatexchange.content_type import content_base
from threatexchange.signal_type import index


class HashComparisonResult(t.NamedTuple):
    match: bool
    distance: int  # TODO - remove

    @classmethod
    def from_match(cls, dist: int = 0) -> "HashComparisonResult":
        return cls(True, dist)

    @classmethod
    def from_no_match(cls, dist: int = 1) -> "HashComparisonResult":
        return cls(False, dist)

    @classmethod
    def from_dist(cls, dist: int, threshold: int) -> "HashComparisonResult":
        return cls(dist <= threshold, dist)

    @classmethod
    def from_bool(cls, matches: bool) -> "HashComparisonResult":
        return cls.from_match() if matches else cls.from_no_match()


class SignalType:
    """
    Abstraction for different signal types.

    A signal type is an intermediate representation of content that can be used
    to match against similar or identical content. Sometimes called a "hash"
    type.

    This class additionally helps translates ThreatDescriptors into the correct
    representation to do matching, as well as serialize that representation
    into a compact form.

    # Why is `signal_str` str?
    Forcing the type to always be serializable in str gives us the advantage that
    uploading it to SignalAPIs is always straightforward.
    """

    @classmethod
    def get_name(cls):
        """A compact name in lower_with_underscore style (used in filenames)"""
        return common.class_name_to_human_name(cls.__name__, "Signal")

    @classmethod
    def get_content_types(cls) -> t.List[t.Type[content_base.ContentType]]:
        """Which content types this Signal applies to (usually just one)"""
        raise NotImplementedError

    @classmethod
    def get_index_cls(cls) -> t.Type[index.SignalTypeIndex]:
        """Return the index class that handles this signal type"""
        # Confused about which one to start with?
        # Make a subclass of:
        #   1. TrivialLinearSearchHashIndex: Just use compare_hash
        #   2. TrivialLinearSearchMatchIndex: If you are MatchesStr
        # Or if you only support exact matching (like MD5):
        #   3. TrivialSignalTypeIndex
        raise NotImplementedError

    @classmethod
    def compare_hash(cls, hash1: str, hash2: str) -> HashComparisonResult:
        """
        Compare the distance of two hashes, the key operation for matching.

        Note that this can just be a reference/helper, and the efficient
        version of the algorithm can live in the index class.
        """
        raise NotImplementedError

    @classmethod
    def validate_signal_str(cls, signal_str: str) -> str:
        """
        Return a normalized version the signal or throws an exception if malformed
        """
        if not signal_str:
            raise ValueError("empty hash")
        return signal_str.strip()

    @staticmethod
    def get_examples() -> t.List[str]:
        """
        Return example signals, which can be used for tests or demos.

        Strings returned by this class are automatically pulled in by the
        StaticSampleSignalExchangeAPI, which it will "fetch" and build
        indices for if the Signal is enabled.
        """
        return []


class FileHasher:
    """
    This class can hash files.
    """

    @classmethod
    def hash_from_file(cls, file: pathlib.Path) -> str:
        """
        Get a string representation of the hash from a file.

        If a hash cannot be generated, empty string should be returned.
        """
        raise NotImplementedError


class TextHasher(FileHasher):
    """
    This class can turn text into intermediary representations (hashes)
    """

    @classmethod
    def hash_from_str(cls, text: str) -> str:
        """
        Get a string representation of the hash from a string.

        If a hash cannot be generated, empty string should be returned.
        """
        raise NotImplementedError

    @classmethod
    def hash_from_file(cls, file: pathlib.Path) -> str:
        return cls.hash_from_str(file.read_text())


class MatchesStr:
    @classmethod
    def matches_str(cls, signal: str, haystack: str) -> HashComparisonResult:
        """
        Compare the distance of two hashes, the key operation for matching.

        Note that this can just be a reference/helper, and the efficient
        version of the algorithm can live in the index class.
        """
        raise NotImplementedError


class BytesHasher(FileHasher):
    """
    This class can hash bytes.
    """

    @classmethod
    def hash_from_bytes(cls, bytes_: bytes) -> str:
        """
        Get a string representation of the hash from bytes.

        If a hash cannot be generated, empty string should be returned.
        """
        raise NotImplementedError

    @classmethod
    def hash_from_file(cls, file: pathlib.Path) -> str:
        return cls.hash_from_bytes(file.read_bytes())


class SimpleSignalType(SignalType):
    """
    Dead simple implementation for loading/storing a SignalType.

    Assumes that the signal type can easily merge on a string.
    """

    @classmethod
    def compare_hash(cls, hash1: str, hash2: str) -> HashComparisonResult:
        return HashComparisonResult.from_bool(hash1 == hash2)


class TrivialSignalTypeIndex(index.SignalTypeIndex[index.T]):
    """
    Index that does only exact matches
    """

    def __init__(self) -> None:
        self.state: t.Dict[str, t.List[index.T]] = {}

    def query(self, query: str) -> t.List[index.IndexMatch[index.T]]:
        return [index.IndexMatch(0, meta) for meta in self.state.get(query, [])]

    def add(self, signal_str: str, entry: index.T) -> None:
        l = self.state.get(signal_str)
        if not l:
            l = []
            self.state[signal_str] = l
        l.append(entry)


class TrivialLinearSearchHashIndex(index.SignalTypeIndex[index.T]):
    """
    Index that does a linear search and serializes with pickle

    O(n) is the best n, clearly.
    """

    # You'll have to override with each usecase, because I wasn't sure
    # If pickle would behave expectedly here
    _SIGNAL_TYPE: t.Type[SignalType]

    def __init__(self) -> None:
        self.state: t.List[t.Tuple[str, index.T]] = []

    def query(self, query_hash: str) -> t.List[index.IndexMatch[index.T]]:
        ret = []
        for hash, payload in self.state:
            res = self._SIGNAL_TYPE.compare_hash(hash, query_hash)
            if res.match:
                ret.append(index.IndexMatch(res.distance, payload))
        return ret

    def add(self, signal_str: str, entry: index.T) -> None:
        self.state.append((signal_str, entry))


class TrivialLinearSearchMatchIndex(index.SignalTypeIndex[index.T]):
    """
    Index that does a linear search and serializes with pickle

    O(n) is the best n, clearly.
    """

    # You'll have to override with each usecase
    _SIGNAL_TYPE: t.Type[MatchesStr]

    def __init__(self) -> None:
        self.state: t.List[t.Tuple[str, index.T]] = []
        assert issubclass(self._SIGNAL_TYPE, MatchesStr)

    def query(self, query_hash: str) -> t.List[index.IndexMatch[index.T]]:
        ret = []
        for signal, payload in self.state:
            res = self._SIGNAL_TYPE.matches_str(signal, query_hash)
            if res.match:
                ret.append(index.IndexMatch(res.distance, payload))
        return ret

    def add(self, signal_str: str, entry: index.T) -> None:
        self.state.append((signal_str, entry))
