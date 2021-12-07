#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Core abstractions for signal types.
"""

import csv
import pathlib
import pickle
import typing as t

from .. import common
from ..descriptor import SimpleDescriptorRollup, ThreatDescriptor
from . import index


class TrivialSignalTypeIndex(index.SignalTypeIndex):
    """
    Index that does only exact matches and serializes with pickle
    """

    def __init__(self) -> None:
        self.state: t.Dict[str, t.List[t.Any]] = {}

    def query(self, hash: str) -> t.List[index.IndexMatch[index.T]]:
        return [index.IndexMatch(0, meta) for meta in self.state.get(hash, [])]

    def add(self, vals: t.Iterable[t.Tuple[str, t.Any]]) -> None:
        for k, val in vals:
            l = self.state.get(k)
            if not l:
                l = []
                self.state[k] = l
            l.append(val)

    @classmethod
    def build(cls, vals: t.Iterable[t.Tuple[str, t.Any]]):
        ret = cls()
        ret.add(vals=vals)
        return ret

    def serialize(self, fout: t.BinaryIO):
        pickle.dump(self, fout)

    @classmethod
    def deserialize(cls, fin: t.BinaryIO):
        return pickle.load(fin)


class SignalMatch(t.NamedTuple):
    # TODO - Labels probably don't belong here, because we just duplicate storage
    #        better to have descriptor lookup with the full labels
    labels: t.Set[str]
    primary_descriptor_id: int
    # TODO: Someday, also include the following:
    # contested: bool
    # plurality_opinion: t.Tuple(bool, t.Set[str])
    # highest_action_severity: str
    # opinions_by_owner: t.Dict[int, MatchOpinion]


class SignalType:
    """
    Abstraction for different signal types.

    A signal type is an intermediate representation of content that can be used
    to match against similar or identical content. Sometimes called a "hash"
    type.

    This class additionally helps translates ThreatDescriptors into the correct
    representation to do matching, as well as serialize that representation
    into a compact form.
    """

    @classmethod
    def get_name(cls):
        """A compact name in lower_with_underscore style (used in filenames)"""
        return common.class_name_to_human_name(cls.__name__, "Signal")

    @classmethod
    def get_index_cls(cls) -> t.Type[index.SignalTypeIndex]:
        """Return the index class that handles this signal type"""
        return TrivialSignalTypeIndex

    @classmethod
    def indicator_applies(cls, indicator_type: str, tags: t.List[str]) -> bool:
        """Does this indicator correspond to this signal type?"""
        raise NotImplementedError

    @classmethod
    def compare_hash(cls, hash1: str, hash2: str) -> int:
        """
        Compare the distance of two hashes, the key operaiton for matching.

        If the algorithm doesn't support distance, having 0 = match,
        1 = no hash.

        Note that this can just be a reference/helper, and the efficient
        version of the algorithm can live in the index class.
        """
        raise NotImplementedError

    ##########################################################################
    # TODO - Remove  these methods after refactor
    def process_descriptor(self, descriptor: ThreatDescriptor) -> bool:
        """
        Add ThreatDescriptor to the state of this type, if it is for this type.

        Return true if the true if the descriptor was used.
        """
        return False

    def load(self, path: pathlib.Path) -> None:
        raise NotImplementedError

    def store(self, path: pathlib.Path) -> None:
        raise NotImplementedError


class HashMatcher:
    def match_hash(self, hash: str) -> t.List[SignalMatch]:
        """
        Given a representation of this SignalType, return matches.

        Example - PDQ distance comparison, or MD5 exact comparison
        """
        raise NotImplementedError


class FileMatcher:
    def match_file(self, file: pathlib.Path) -> t.List[SignalMatch]:
        """
        Given a file containing content, return matches.
        """
        raise NotImplementedError


class BytesMatcher:
    def match_bytes(self, bytes_: bytes) -> t.List[SignalMatch]:
        """
        If you have already brought the file to memory, don't write it to disk,
        hash it right there.
        """
        raise NotImplementedError


class StrMatcher(FileMatcher):
    def match(self, content: str) -> t.List[SignalMatch]:
        """
        Given a string representation of content, return matches.

        You don't need to implement this if it doesn't make sense for your
        signal type.
        """
        raise NotImplementedError

    def match_file(self, path: pathlib.Path) -> t.List[SignalMatch]:
        return self.match(path.read_text())


class StrHasher(HashMatcher, StrMatcher):
    """
    This class can turn text into intermediary representations (hashes)
    """

    @classmethod
    def hash_from_str(cls, content: str) -> str:
        """Get a string representation of the hash from a string"""
        raise NotImplementedError

    def match(self, content: str) -> t.List[SignalMatch]:
        str_hash = self.hash_from_str(content)
        return self.match_hash(str_hash)


class FileHasher(HashMatcher, FileMatcher):
    """
    This class can hash files.

    If also inheiriting from StrHasher, put this second in the inheiretence
    to prefer file hashing to reading the file in as a Str.
    """

    @classmethod
    def hash_from_file(self, file: pathlib.Path) -> str:
        """Get a string representation of the hash from a file"""
        raise NotImplementedError

    def match_file(self, path: pathlib.Path) -> t.List[SignalMatch]:
        file_hash = self.hash_from_file(path)
        return self.match_hash(file_hash)


class BytesHasher(HashMatcher, BytesMatcher):
    """
    This class can hash bytes.
    """

    @classmethod
    def hash_from_bytes(self, bytes_: bytes) -> str:
        """Get a string representation of the hash from bytes."""
        raise NotImplementedError

    def match_bytes(self, bytes_: bytes) -> t.List[SignalMatch]:
        bytes_hash = self.hash_from_bytes(bytes_)
        return self.match_hash(bytes_hash)


class SimpleSignalType(SignalType, HashMatcher):
    """
    Dead simple implementation for loading/storing a SignalType.

    Assumes that the signal type can easily merge on a string.
    """

    INDICATOR_TYPE: t.Union[str, t.Tuple[str, ...]] = ()
    TYPE_TAG: t.Optional[str] = None

    @classmethod
    def indicator_applies(cls, indicator_type: str, tags: t.List[str]) -> bool:
        types = cls.INDICATOR_TYPE
        if isinstance(cls.INDICATOR_TYPE, str):
            types = (cls.INDICATOR_TYPE,)
        if indicator_type not in types:
            return False
        if cls.TYPE_TAG is not None:
            return cls.TYPE_TAG in tags
        return True

    @classmethod
    def compare_hash(cls, hash1: str, hash2: str) -> int:
        if hash1 == hash2:
            return 0
        return 1

    ##########################################################################
    # TODO - Remove these methods after refactor
    def __init__(self) -> None:
        self.state: t.Dict[str, SimpleDescriptorRollup] = {}

    def process_descriptor(self, descriptor: ThreatDescriptor) -> bool:
        """
        Add ThreatDescriptor to the state of this type, if it is for this type

        Return true if the true if the descriptor was used.
        """
        if not self.indicator_applies(descriptor.indicator_type, descriptor.tags):
            return False
        old_val = self.state.get(descriptor.raw_indicator)
        if old_val is None:
            self.state[
                descriptor.raw_indicator
            ] = SimpleDescriptorRollup.from_descriptor(descriptor)
        else:
            old_val.merge(descriptor)
        return True

    def match_hash(self, signal_str: str) -> t.List[SignalMatch]:
        found = self.state.get(signal_str)
        if found:
            return [SignalMatch(found.labels, found.first_descriptor_id)]
        return []

    def load(self, path: pathlib.Path) -> None:
        self.state.clear()
        csv.field_size_limit(path.stat().st_size)  # dodge field size problems
        with path.open("r", newline="") as f:
            for row in csv.reader(f):
                self.state[row[0]] = SimpleDescriptorRollup.from_row(row[1:])

    def store(self, path: pathlib.Path) -> None:
        with path.open("w+", newline="") as f:
            writer = csv.writer(f)
            for k, v in self.state.items():
                writer.writerow((k,) + v.as_row())
