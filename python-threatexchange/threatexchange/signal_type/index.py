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
    """
    Wrapper around a match to the index, which may or may not
    be an actual match based on the distance settings for a source.

    The index is free to optimize not returning values that are
    greater than would be considered matches by a downstream (i.e.
    31 is probably the max distance that would be used in PDQ)

    NamedTuple can't be made generic, so here's an equivalent
    """

    __slots__ = ["distance", "metadata"]
    distance: int
    metadata: T

    def __init__(self, distance: int, metadata: T) -> None:
        self.distance = distance
        self.metadata = metadata


class SignalTypeIndex(t.Generic[T]):
    """
    Abstraction for an efficient matching technique.

    This class can be thought of as just a Dict[hash, List[T]] interface
    that can return the flattened result of multiple entries on a get().

    The T can be whatever metadata might be useful, although be warned
    that not all T may serialize correctly.

    # Why is `hash` str?
    There are various multi-pass hashing approaches that may generate more
    complicated data structures, or require multiple query passes. It's
    unclear whether we should try and generalize those yet, and forcing the
    type to always be serializable in str gives us the advantage that
    uploading it to ThreatExchange is always straightforward.

    # Handling Restricted Value Types
    In cases where your underlying index has limited type support for
    values (i.e. FAISS seems to only support ints), the easiest workaround
    is to just generate your own internal ids and maintain a separate map of
    the real results.

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

        The index is free to optimize not returning values that are
        greater than would be considered matches by a downstream system
        (i.e. 31 is probably the max distance that would be used in PDQ)
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

    def add(cls, entries: t.Iterable[t.Tuple[str, T]]) -> None:
        """
        Add entries to an existing index. May contain elements already in the
        index.
        """
        raise NotImplementedError

    def serialize(self, fout: t.BinaryIO) -> None:
        """
        Convert the index into a bytestream (probably a file).

        The reason to use an IO instead of just stringifying it is that some
        indices might be really big, and we don't want to pay a cost of 2x-ing
        our memory storage (versus writing to file).

        Could also be premature optimization, you decide!
        """
        raise NotImplementedError

    @classmethod
    def deserialize(cls, fin: t.BinaryIO) -> "SignalTypeIndex[T]":
        """Instanciate an index from a previous call to serialize"""
        raise NotImplementedError
