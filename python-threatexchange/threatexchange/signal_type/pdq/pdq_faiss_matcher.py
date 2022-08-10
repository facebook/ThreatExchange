# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import typing as t
import faiss
import binascii
import numpy
from abc import ABC, abstractmethod

from threatexchange.signal_type.pdq.pdq_utils import BITS_IN_PDQ

PDQ_HASH_TYPE = t.Union[str, bytes]


def uint64_to_int64(as_uint64: int):
    """
    Returns the int64 number represented by the same byte representation as the the provided integer if it was understood to
    be a uint64 value.
    """
    return numpy.uint64(as_uint64).astype(numpy.int64).item()


def int64_to_uint64(as_int64: int):
    """
    Returns the uint64 number represented by the same byte representation as the the provided integer if it was understood to
    be a int64 value.
    """
    return numpy.int64(as_int64).astype(numpy.uint64).item()


class PDQHashIndex(ABC):
    @abstractmethod
    def __init__(self, faiss_index: faiss.IndexBinary) -> None:
        self.faiss_index = faiss_index
        super().__init__()

    @abstractmethod
    def hash_at(self, idx: int) -> str:
        """
        Returns the hash located at the given index. The index order is determined by the initial order of hashes used to
        create this index.
        """
        pass

    @abstractmethod
    def add(self, hashes: t.Iterable[PDQ_HASH_TYPE], custom_ids: t.Iterable[int]):
        """
        Adds hashes and their custom ids to the PDQ index.
        """
        pass

    def search(
        self,
        queries: t.Sequence[PDQ_HASH_TYPE],
        threshhold: int,
        return_as_ids: bool = False,
    ):
        """
        Searches this index for PDQ hashes within the index that are no more than the threshold away from the query hashes by
        hamming distance.

        Parameters
        ----------
        queries: sequence of PDQ Hashes
            The PDQ hashes to query against the index
        threshold: int
            Threshold value to use for this search. The hamming distance between the result hashes and the related query will
            be no more than the threshold value. i.e., hamming_dist(q_i,r_i_j) <= threshold.
        return_as_ids: boolean
            whether the return values should be the index ids for the matching items. Defaults to false.

        Returns
        -------
        sequence of matches per query
            For each query provided in queries, the returned sequence will contain a sequence of matches within the index
            that were within threshold hamming distance of that query. These matches will either be a hexstring of the hash
            by default, or the index ids of the matches if `return_as_ids` is True. The inner sequences may be empty in the
            case of no hashes within the index. The same PDQ hash may also appear in more than one inner sequence if it
            matches multiple query hashes.

            For example the hash "000000000000000000000000000000000000000000000000000000000000FFFF" would match both
            "00000000000000000000000000000000000000000000000000000000FFFFFFFF" and
            "0000000000000000000000000000000000000000000000000000000000000000" for a threshold of 16. Thus it would appear in
            the entry for both the hashes if they were both in the queries list.
        """
        query_vectors = [
            numpy.frombuffer(binascii.unhexlify(q), dtype=numpy.uint8) for q in queries
        ]
        qs = numpy.array(query_vectors)
        limits, _, I = self.faiss_index.range_search(qs, threshhold + 1)

        if return_as_ids:
            # for custom ids, we understood them initially as uint64 numbers and then coerced them internally to be signed
            # int64s, so we need to reverse this before returning them back to the caller. For non custom ids, this will
            # effectively return the same result
            output_fn: t.Callable[[int], t.Any] = int64_to_uint64
        else:
            output_fn = self.hash_at

        return [
            [output_fn(idx.item()) for idx in I[limits[i] : limits[i + 1]]]
            for i in range(len(query_vectors))
        ]

    def search_with_distance_in_result(
        self,
        queries: t.Sequence[str],
        threshhold: int,
    ) -> t.Dict[str, t.List[t.Tuple[int, str, numpy.float32]]]:
        """
        Search method that return a mapping from query_str =>  (id, hash, distance)

        This implementation is the same as `search` above however instead of returning just the sequence of matches
        per query it returns a mapping from query strings to a list of matched hashes (or ids) and distances

        e.g.
        result = {
            "000000000000000000000000000000000000000000000000000000000000FFFF": [
                (12345678901, "00000000000000000000000000000000000000000000000000000000FFFFFFFF", 16.0)
            ]
        }
        """

        query_vectors = [
            numpy.frombuffer(binascii.unhexlify(q), dtype=numpy.uint8) for q in queries
        ]
        qs = numpy.array(query_vectors)
        limits, similarities, I = self.faiss_index.range_search(qs, threshhold + 1)

        # for custom ids, we understood them initially as uint64 numbers and then coerced them internally to be signed
        # int64s, so we need to reverse this before returning them back to the caller. For non custom ids, this will
        # effectively return the same result
        output_fn: t.Callable[[int], t.Any] = int64_to_uint64

        result = {}
        for i, query in enumerate(queries):
            match_tuples = []
            matches = [idx.item() for idx in I[limits[i] : limits[i + 1]]]
            distances = [idx for idx in similarities[limits[i] : limits[i + 1]]]
            for match, distance in zip(matches, distances):
                # (Id, Hash, Distance)
                match_tuples.append((output_fn(match), self.hash_at(match), distance))
            result[query] = match_tuples
        return result

    def __getstate__(self):
        data = faiss.serialize_index_binary(self.faiss_index)
        return data

    def __setstate__(self, data):
        self.faiss_index = faiss.deserialize_index_binary(data)


class PDQFlatHashIndex(PDQHashIndex):
    """
    Wrapper around an faiss binary index for use with searching for similar PDQ hashes

    The "flat" variant uses an exhaustive search approach that may use less memory than other approaches and may be more
    performant when using larger thresholds for PDQ similarity.
    """

    def __init__(self):
        faiss_index = faiss.IndexBinaryIDMap2(
            faiss.index_binary_factory(BITS_IN_PDQ, "BFlat")
        )
        super().__init__(faiss_index)

    def add(self, hashes: t.Iterable[PDQ_HASH_TYPE], custom_ids: t.Iterable[int]):
        """
        Parameters
        ----------
        hashes: sequence of PDQ Hashes
            The PDQ hashes to create the index with
        custom_ids: sequence of custom ids for the PDQ Hashes
            Sequence of custom id values to use for the PDQ hashes for any
            method relating to indexes (e.g., hash_at). If provided, the nth item in
            custom_ids will be used as the id for the nth hash in hashes. If not provided
            then the ids for the hashes will be assumed to be their respective index
            in hashes (i.e., the nth hash would have id n, starting from 0).
        """
        hash_bytes = [binascii.unhexlify(hash) for hash in hashes]
        vectors = list(
            map(lambda h: numpy.frombuffer(h, dtype=numpy.uint8), hash_bytes)
        )
        i64_ids = list(map(uint64_to_int64, custom_ids))
        self.faiss_index.add_with_ids(numpy.array(vectors), numpy.array(i64_ids))

    def hash_at(self, idx: int) -> str:
        i64_id = uint64_to_int64(idx)
        vector = self.faiss_index.reconstruct(i64_id)
        return binascii.hexlify(vector.tobytes()).decode()


class PDQMultiHashIndex(PDQHashIndex):
    """
    Wrapper around an faiss binary index for use with searching for similar PDQ hashes

    The "multi" variant uses an the Multi-Index Hashing searching technique employed by faiss's
    IndexBinaryMultiHash binary index.

    Properties:
    nhash: int (optional)
    Optional number of hashmaps for the underlaying faiss index to use for
    the Multi-Index Hashing lookups.
    """

    def __init__(self, nhash: int = 16):
        bits_per_hashmap = BITS_IN_PDQ // nhash
        faiss_index = faiss.IndexBinaryIDMap2(
            faiss.IndexBinaryMultiHash(BITS_IN_PDQ, nhash, bits_per_hashmap)
        )
        super().__init__(faiss_index)
        self.__construct_index_rev_map()

    def add(
        self,
        hashes: t.Iterable[PDQ_HASH_TYPE],
        custom_ids: t.Iterable[int],
    ):
        """
        Parameters
        ----------
        hashes: sequence of PDQ Hashes
            The PDQ hashes to create the index with
        custom_ids: sequence of custom ids for the PDQ Hashes
            Sequence of custom id values to use for the PDQ hashes for any
            method relating to indexes (e.g., hash_at). If provided, the nth item in
            custom_ids will be used as the id for the nth hash in hashes. If not provided
            then the ids for the hashes will be assumed to be their respective index
            in hashes (i.e., the nth hash would have id n, starting from 0).

        Returns
        -------
        a PDQMultiHashIndex of these hashes
        """
        hash_bytes = [binascii.unhexlify(hash) for hash in hashes]
        vectors = list(
            map(lambda h: numpy.frombuffer(h, dtype=numpy.uint8), hash_bytes)
        )
        i64_ids = list(map(uint64_to_int64, custom_ids))
        self.faiss_index.add_with_ids(numpy.array(vectors), numpy.array(i64_ids))
        self.__construct_index_rev_map()

    @property
    def mih_index(self):
        """
        Convenience accessor for the underlaying faiss.IndexBinaryMultiHash index regardless of if it is wrapped in an ID
        map or not.
        """
        if hasattr(self.faiss_index, "index"):
            return faiss.downcast_IndexBinary(self.faiss_index.index)
        return self.faiss_index

    def search(
        self,
        queries: t.Sequence[PDQ_HASH_TYPE],
        threshhold: int,
        return_as_ids: bool = False,
    ):
        self.mih_index.nflip = threshhold // self.mih_index.nhash
        return super().search(queries, threshhold, return_as_ids)

    def search_with_distance_in_result(
        self,
        queries: t.Sequence[str],
        threshhold: int,
    ):
        self.mih_index.nflip = threshhold // self.mih_index.nhash
        return super().search_with_distance_in_result(queries, threshhold)

    def hash_at(self, idx: int) -> str:
        i64_id = uint64_to_int64(idx)
        if self.index_rev_map:
            index_id = self.index_rev_map[i64_id]
        else:
            index_id = i64_id
        vector = self.mih_index.storage.reconstruct(index_id)
        return binascii.hexlify(vector.tobytes()).decode()

    def __construct_index_rev_map(self):
        """
        Workaround method for creating an in-memory lookup mapping custom ids to internal index id representations. The
        rev_map property provided in faiss.IndexBinaryIDMap2 has no accessible `at` or other index lookup methods in swig
        and the implementation of `reconstruct` in faiss.IndexBinaryIDMap2 requires the underlaying index to directly
        support `reconstruct`, which faiss.IndexBinaryMultiHash does not. Thus this workaround is needed until either the
        values in the faiss.IndexBinaryIDMap2 rev_map can be accessed directly or faiss.IndexBinaryMultiHash is directly
        supports `reconstruct` calls.
        """
        if hasattr(self.faiss_index, "id_map"):
            id_map = self.faiss_index.id_map
            self.index_rev_map = {id_map.at(i): i for i in range(id_map.size())}
        else:
            self.index_rev_map = None

    def __setstate__(self, data):
        super().__setstate__(data)
        self.__construct_index_rev_map()
