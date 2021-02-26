# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Implementation of SignalTypeIndex abstraction for PDQ by wrapping hashing.pdq_faiss_matcher.
"""

import typing as t
import pickle

from threatexchange.signal_type.index import SignalTypeIndex, IndexMatch
from threatexchange.hashing.pdq_faiss_matcher import PDQMultiHashIndex

T = t.TypeVar("T")
PDQ_CONFIDENT_MATCH_THRESHOLD = 31


class PDQIndex(SignalTypeIndex):
    """
    Wrapper around the pdq faiss index lib
    """

    def __init__(self, entries: t.Iterable[t.Tuple[str, T]]) -> None:
        super().__init__()
        self.local_id_to_entry = dict()
        hashes = list()
        for i in range(len(entries)):
            self.local_id_to_entry[i] = entries[i]
            hashes.append(entries[i][0])
        self.index = PDQMultiHashIndex.create(
            hashes, custom_ids=self.local_id_to_entry.keys()
        )

    def query(self, hash: str) -> t.List[IndexMatch[T]]:
        """
        Look up entries against the index, up to the max supported distance.
        """
        results = self.index.search(
            [hash], PDQ_CONFIDENT_MATCH_THRESHOLD, return_as_ids=True
        )
        matches = list()
        for result_ids in results:
            for id in result_ids:
                # distance = -1 (index does not currently support distance)
                matches.append(IndexMatch(-1, self.local_id_to_entry[id][1]))
        return matches

    @classmethod
    def build(cls, entries: t.Iterable[t.Tuple[str, T]]) -> "SignalTypeIndex[T]":
        """
        Build an PDQ index from a set of entries.
        """
        return PDQIndex(entries)

    def serialize(self, fout: t.BinaryIO) -> None:
        """
        Convert the PDQ index into a bytestream (probably a file).
        """
        return pickle.dumps(self)

    @classmethod
    def deserialize(cls, fin: t.BinaryIO) -> "SignalTypeIndex[T]":
        """
        Instanciate an index from a previous call to serialize
        """
        return pickle.loads(fin)
