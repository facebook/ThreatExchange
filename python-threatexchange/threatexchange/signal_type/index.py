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

from dataclasses import dataclass
import pickle
import typing as t


T = t.TypeVar("T")
S_Co = t.TypeVar("S_Co", covariant=True, bound="SignalSimilarityInfo")
CT = t.TypeVar("CT", bound="Comparable")


class Comparable(t.Protocol):
    """Helper for annotating comparable types."""

    def __lt__(self: CT, other: CT) -> bool:
        pass

    def __le__(self: CT, other: CT) -> bool:
        pass


NO_DISTANCE_STR = "-"


class SignalSimilarityInfo:
    """
    Metadata with context about a comparison between content or signals.

    This can be used for logging and debugging, but could also be re-used
    as an argument to match functions to use as thresholds.

    This information often is treated as a distance, and so comparison
    operators
    """

    def __lt__(self, other: t.Any) -> bool:
        if isinstance(other, SignalSimilarityInfoWithSingleDistance):
            return False  # < operator valid, but by default, not ordered
        return NotImplemented

    def __le__(self, other: t.Any) -> bool:
        # Provide a default impl
        return self < other or self == other

    # Don't define __gt__ or __ge__ because of unexpected interactions with
    # functools.total_ordering
    def pretty_str(self) -> str:
        """
        A short string without whitespace about a match with more context.

        See it in action on the CLI in `threatexchange match`.
        """
        return NO_DISTANCE_STR


@dataclass
# @functools.total_ordering
# Can't use yet, need to move library mypy past
# https://github.com/python/mypy/issues/11728
class SignalSimilarityInfoWithSingleDistance(t.Generic[CT], SignalSimilarityInfo):
    distance: CT

    def pretty_str(self) -> str:
        return str(self.distance)

    def _comparable(
        self, other: t.Any
    ) -> t.Optional["SignalSimilarityInfoWithSingleDistance[CT]"]:
        if isinstance(other, SignalSimilarityInfoWithSingleDistance):
            if isinstance(self.distance, other.distance.__class__):
                return other
        return None

    def __lt__(self, other: t.Any) -> bool:
        checked = self._comparable(other)
        if checked is None:
            return NotImplemented
        return self.distance < checked.distance

    def __eq__(self, other: object) -> bool:
        checked = self._comparable(other)
        if checked is None:
            return super().__eq__(other)
        return self.distance == checked.distance


SignalSimilarityInfoWithIntDistance = SignalSimilarityInfoWithSingleDistance[int]


class IndexMatchUntyped(t.Generic[S_Co, T]):
    """
    Wrapper around a match to the index, which may or may not
    be an actual match based on the distance settings for a source.

    The index is free to optimize not returning values that are
    greater than would be considered matches by a downstream (i.e.
    31 is probably the max distance that would be used in PDQ)

    NamedTuple can't be made generic, so here's an equivalent
    """

    __slots__ = ["similarity_info", "metadata"]
    similarity_info: S_Co
    metadata: T

    def __init__(self, similarity_info: S_Co, metadata: T) -> None:
        self.similarity_info = similarity_info
        self.metadata = metadata

    def __eq__(self, other: t.Any) -> bool:
        if isinstance(other, IndexMatchUntyped):
            return (
                self.similarity_info == other.similarity_info
                and self.metadata == other.metadata
            )
        return super().__eq__(other)


IndexMatch = IndexMatchUntyped[SignalSimilarityInfo, T]


Self = t.TypeVar("Self", bound="SignalTypeIndex")


class SignalTypeIndex(t.Generic[T]):
    """
    Abstraction for efficient scale matching on signals.

    SignalType forces you to implement the brute force approaches to
    make them easier to work with and conceptualize. However, if you
    are intending to match thousands of items a second at the scale of
    millions of signals, this class allows you to implement a more
    complex and efficient method.

    This class can be thought of as just a Dict[hash, List[T]] interface
    that can return the flattened result of multiple entries on a get().

    The T can be whatever metadata might be useful, although be warned
    that not all T may serialize correctly.

    # Handling Index Types that cannot be updated
    The default interface assumes that you can both create and update
    indices. It's possible that some storage types cannot support this.
    In that case build() and deserialize() are the only methods that
    should be used to create indices, and you can have add() methods
    throw NotImplementedError.

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

    # TODO - this doesn't handle bytes queries / BytesHashers
    def query(self, query: str) -> t.Sequence[IndexMatch[T]]:
        """
        Look up entries against the index, up to the max supported distance.

        The index is free to optimize not returning values that are
        greater than would be considered matches by a downstream system
        (i.e. 31 is probably the max distance that would be used in PDQ)
        """
        raise NotImplementedError

    @classmethod
    def build(cls: t.Type[Self], entries: t.Iterable[t.Tuple[str, T]]) -> Self:
        """
        Build an index from a set of entries.

        You can override __init__ as needed, but keep this once constant.

        Note that there may be duplicates of the hash type, i.e.

        H1: M1
        H1: M2

        A later call to query(H1) should return both M1 and M2
        """
        ret = cls()
        ret.add_all(entries)
        return ret

    # TODO - probably move add() methods to a mixin instead
    def add(self, signal_str: str, entry: T) -> None:
        """
        Add an entry to the index.

        Duplicate entries should not replace previous ones.
        """
        raise NotImplementedError

    def add_all(self, entries: t.Iterable[t.Tuple[str, T]]) -> None:
        """add, but more so"""
        for signal_str, entry in entries:
            self.add(signal_str, entry)

    def serialize(self, fout: t.BinaryIO) -> None:
        """
        Convert the index into a bytestream (probably a file).

        The reason to use an IO instead of just stringifying it is that some
        indices might be really big, and we don't want to pay a cost of 2x-ing
        our memory storage (versus writing to file).

        Could also be premature optimization, you decide!
        """
        fout.write(pickle.dumps(self))

    @classmethod
    def deserialize(cls: t.Type[Self], fin: t.BinaryIO) -> Self:
        """Instanciate an index from a previous call to serialize"""
        return pickle.loads(fin.read())
