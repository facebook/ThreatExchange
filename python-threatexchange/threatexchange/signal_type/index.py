#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Abstraction around efficient scaled matching of SignalTypes

This usually involves build an efficient datastructure for lookups
(aka, an index).

At scale, the flow for matching looks something like:
1. Fetch information from API, store it locally
2. Process local copy of the information, separate it out by
   which system will consume it
3. Build indices for distribution (or deltas to those indices if
   you are really fancy)
4. In the service that does matching, swap out the index to the
   new one.
5. Hash content at upload sites, check against the service hosting
   the index.

"""

import typing as t


T = t.TypeVar("T")


class IndexMatch(t.Generic[T]):

    __slots__ = ["distance", "metadata"]
    distance: int
    metadata: T

    def __init__(self, distance: int, metadata: T) -> None:
        self.distance = distance


class SignalTypeIndex(t.Generic[T]):
    """
    Abstraction for an efficient matching technique.

    This class can be thought of as just a Dict[hash, List[T]] interface
    that can return the flattened result of multiple entries on a get().

    The T can be whatever metadata might be useful, although be warned
    that not all T may serialize correctly.

    In cases where your underlying index has limited type support for
    values, the easiest workaround is to just generate your own
    internal ids and maintain a separate map of the real results.

    fancy_index_only_to_int[str, int]
    internal_mapping List[T] or Dict[int, T]

    def get(hash: str):
        matches = fancy_index_only_to_int[str]
        ret = []
        for idx in matches:
            entry = internal_mapping[idx]
            ret.append(entry)
        return ret

    def add(hash: str, meta: T):
        idx = fancy_index_only_to_int.put(hash)
        internal_mapping[idx] = meta
    """

    def query(self, hash: str) -> t.List[IndexMatch[T]]:
        """
        Look up entries against the index, up to the max supported distance.
        """
        raise NotImplementedError

    @classmethod
    def build(cls, entries: t.Iterable[t.Tuple[str, T]]) -> "SignalTypeIndex[T]":
        """
        Build an index from a set of entries.

        Note that there may be duplicates of the hash type, i.e.

        H1: M1
        H1: M2

        A later call to query(H1) should return both M1 and M2
        """
        raise NotImplementedError

    def serialize(self, fout: t.BinaryIO) -> None:
        """Convert the index into a bytestream (probably a file)"""
        raise NotImplementedError

    @classmethod
    def deserialize(cls, fin: t.BinaryIO) -> "SignalTypeIndex[T]":
        """Instanciate an index from a previous call to serialize"""
        raise NotImplementedError
