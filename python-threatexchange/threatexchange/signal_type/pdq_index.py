# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Implementation of SignalTypeIndex abstraction for PDQ by wrapping
hashing.pdq_faiss_matcher.
"""

from collections import OrderedDict
import collections
import typing as t
import pickle

from threatexchange.signal_type.index import SignalTypeIndex, IndexMatch, T as IndexT
from threatexchange.hashing.pdq_faiss_matcher import (
    PDQHashIndex,
    PDQMultiHashIndex,
    PDQFlatHashIndex,
)


class PDQIndex(SignalTypeIndex):
    """
    Wrapper around the pdq faiss index lib
    using PDQMultiHashIndex
    """

    PDQ_CONFIDENT_MATCH_THRESHOLD = 31
    T = IndexT

    @classmethod
    def _get_empty_index(cls) -> PDQHashIndex:
        return PDQMultiHashIndex()

    def __init__(self, entries: t.Iterable[t.Tuple[str, IndexT]]) -> None:
        super().__init__()
        self.local_id_to_entry: t.OrderedDict = collections.OrderedDict()
        self.index: PDQHashIndex = self._get_empty_index()
        self.add(entries=entries)

    def __len__(self) -> int:
        return len(self.local_id_to_entry)

    def query(
        self, hash: str, threshhold=PDQ_CONFIDENT_MATCH_THRESHOLD
    ) -> t.List[IndexMatch[IndexT]]:
        """
        Look up entries against the index, up to the max supported distance.
        """

        # query takes a signal hash but index supports batch queries hence [hash]
        results = self.index.search([hash], threshhold, return_as_ids=True)
        matches = []
        for result_ids in results:
            for id in result_ids:
                # distance = -1 (index does not currently support distance)
                matches.append(IndexMatch(-1, self.local_id_to_entry[id][1]))
        return matches

    def add(self, entries: t.Iterable[t.Tuple[str, IndexT]]) -> None:
        hashes = []

        for i, entry in enumerate(entries):
            self.local_id_to_entry[i] = entry
            hashes.append(entry[0])

        self.index.add(hashes, self.local_id_to_entry.keys())

    @classmethod
    def build(
        cls,
        entries: t.Iterable[t.Tuple[str, IndexT]],
    ) -> "SignalTypeIndex[IndexT]":
        """
        Build an PDQ index from a set of entries.
        """
        return cls(entries)

    def serialize(self, fout: t.BinaryIO) -> None:
        """
        Convert the PDQ index into a bytestream (probably a file).
        """
        fout.write(pickle.dumps(self))

    @classmethod
    def deserialize(cls, fin: t.BinaryIO) -> "SignalTypeIndex[IndexT]":
        """
        Instantiate an index from a previous call to serialize
        """
        return pickle.loads(fin.read())


class PDQFlatIndex(PDQIndex):
    """
    Wrapper around the pdq faiss index lib
    that uses PDQFlatHashIndex instead of PDQMultiHashIndex
    """

    @classmethod
    def _get_empty_index(cls) -> PDQHashIndex:
        return PDQFlatHashIndex()
