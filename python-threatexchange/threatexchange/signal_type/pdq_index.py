# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Implementation of SignalTypeIndex abstraction for PDQ by wrapping
hashing.pdq_faiss_matcher.
"""

import typing as t
import pickle

from threatexchange.signal_type.index import SignalTypeIndex, IndexMatch, T as IndexT
from threatexchange.hashing.pdq_faiss_matcher import PDQMultiHashIndex


class PDQIndex(SignalTypeIndex):
    """
    Wrapper around the pdq faiss index lib
    """

    PDQ_CONFIDENT_MATCH_THRESHOLD = 31
    T = IndexT

    def __init__(self, entries: t.Iterable[t.Tuple[str, T]]) -> None:
        super().__init__()
        self.local_id_to_entry = {}
        hashes = []
        for i, entry in enumerate(entries):
            self.local_id_to_entry[i] = entry
            hashes.append(entry[0])
        self.index = PDQMultiHashIndex.create(
            hashes, custom_ids=self.local_id_to_entry.keys()
        )

    def __len__(self) -> int:
        return len(self.local_id_to_entry)

    def query(self, hash: str) -> t.List[IndexMatch[T]]:
        """
        Look up entries against the index, up to the max supported distance.
        """

        # query takes a signal hash but index supports banch quries hence [hash]
        results = self.index.search(
            [hash], self.PDQ_CONFIDENT_MATCH_THRESHOLD, return_as_ids=True
        )
        matches = []
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
        fout.write(pickle.dumps(self))

    @classmethod
    def deserialize(cls, fin: t.BinaryIO) -> "SignalTypeIndex[T]":
        """
        Instanciate an index from a previous call to serialize
        """
        return pickle.loads(fin)
