#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Core abstractions for signal types.
"""

import pathlib
import importlib
import typing as t

from threatexchange import common
from threatexchange.content_type import content_base
from threatexchange.signal_type import index


class HashComparisonResult(t.NamedTuple):
    match: bool
    distance: int

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
    def get_content_types(self) -> t.List[t.Type[content_base.ContentType]]:
        """Which content types this Signal applies to (usually just one)"""
        raise NotImplementedError

    @classmethod
    def get_index_cls(cls) -> t.Type[index.SignalTypeIndex]:
        """Return the index class that handles this signal type"""
        return _MagicDefaultSignalTypeIndex.get_index_for_signal_type(cls)

    @classmethod
    def compare_hash(
        cls, hash1: str, hash2: str, distance_threshold: t.Optional[int] = None
    ) -> HashComparisonResult:
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
        @see threatexchange.fetcher.simple.static_sample
        """
        return []


class FileHasher:
    """
    This class can hash files.
    """

    @classmethod
    def hash_from_file(cls, file: pathlib.Path) -> str:
        """Get a string representation of the hash from a file"""
        raise NotImplementedError


class TextHasher(FileHasher):
    """
    This class can turn text into intermediary representations (hashes)
    """

    @classmethod
    def hash_from_str(cls, text: str) -> str:
        """Get a string representation of the hash from a string"""
        raise NotImplementedError

    @classmethod
    def hash_from_file(cls, file: pathlib.Path) -> str:
        return cls.hash_from_str(file.read_text())


class MatchesStr:
    @classmethod
    def matches_str(
        cls, signal: str, haystack: str, distance_threshold: t.Optional[int] = None
    ) -> HashComparisonResult:
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
        """Get a string representation of the hash from bytes."""
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
    def compare_hash(
        cls, hash1: str, hash2: str, distance_threshold: t.Optional[int] = None
    ) -> HashComparisonResult:
        if distance_threshold is not None:
            raise ValueError("distance_threshold not supported")
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


class _MagicDefaultSignalTypeIndex(index.SignalTypeIndex[index.T]):
    """ """

    def __init__(self, signal_type: t.Type[SignalType]) -> None:
        self.state: t.List[t.Tuple[str, index.T]] = []
        self._signal_type: t.Type[SignalType] = signal_type

    @classmethod
    def build(cls, entries: t.Iterable[t.Tuple[str, index.T]]):
        raise NotImplementedError("Should not be called directly")

    def add(self, signal_str: str, entry: index.T) -> None:
        self.state.append((signal_str, entry))

    def is_index_for_signal_type(self, other: SignalType) -> bool:
        return self._signal_type == other

    @classmethod
    def get_index_for_signal_type(
        cls, signal_type: t.Type[SignalType]
    ) -> t.Type[index.SignalTypeIndex[index.T]]:

        parent: t.Type[_MagicDefaultSignalTypeIndex]
        if issubclass(signal_type, MatchesStr):
            parent = _LinearSearchMatchIndex
        else:
            parent = _LinearSearchHashIndex

        class _GeneratedMagicDefaultSignalTypeIndex(parent):  # type: ignore  # too weird for mypy
            @staticmethod
            def build(entries: t.Iterable[t.Tuple[str, index.T]]):
                ret = parent(signal_type)
                ret.add_all(entries)
                return ret

        return _GeneratedMagicDefaultSignalTypeIndex

    def __getstate__(self):
        state = self.__dict__.copy()
        state[
            "_signal_type"
        ] = f"{self._signal_type.__module__}.{self._signal_type.__qualname__}"
        return state

    def __setstate__(self, state) -> None:
        self.__dict__.update(state)
        module_name, _, signal_cls_name = state["_signal_type"].rpartition(".")
        module = importlib.import_module(module_name)
        self._signal_type = getattr(module, signal_cls_name)


class _LinearSearchHashIndex(_MagicDefaultSignalTypeIndex[index.T]):
    """
    Index that does a linear search and serializes with pickle

    O(n) is the best n, clearly.
    """

    def query(self, query_hash: str) -> t.List[index.IndexMatch[index.T]]:
        ret = []
        for hash, payload in self.state:
            res = self._signal_type.compare_hash(hash, query_hash)
            if res.match:
                ret.append(index.IndexMatch(res.distance, payload))
        return ret


class _LinearSearchMatchIndex(_MagicDefaultSignalTypeIndex[index.T]):
    """
    Index that does a linear search and serializes with pickle

    O(n) is the best n, clearly.
    """

    _signal_type: MatchesStr  # type: ignore[assignment]

    def query(self, query_hash: str) -> t.List[index.IndexMatch[index.T]]:
        ret = []
        for signal, payload in self.state:
            res = self._signal_type.matches_str(signal, query_hash)
            if res.match:
                ret.append(index.IndexMatch(res.distance, payload))
        return ret


def is_correct_index_for_signal_type(
    st: t.Type[SignalType], i: index.SignalTypeIndex
) -> bool:
    """
    A validator that takes into account some weirdness with the magic defaults

    Returns true if this is an instance of the correct index type for the
    given signal type.
    """
    if isinstance(i, _MagicDefaultSignalTypeIndex):
        return i._signal_type == st
    else:
        return st.get_index_cls() == i.__class__
