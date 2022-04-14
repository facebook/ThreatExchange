# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Base classes for passing data between SignalExchangeAPIs and other interfaces.

Many implementations will choose to extend these to add additional metadata
needed to power API features.
"""


from dataclasses import dataclass
from enum import IntEnum
from functools import reduce
import typing as t

from threatexchange.fetcher.collab_config import CollaborationConfigBase
from threatexchange.signal_type.signal_base import SignalType

Self = t.TypeVar("Self")


@dataclass
class FetchCheckpointBase:
    """
    If you need to store checkpoint information, this is the place to do it
    """

    def is_stale(self) -> bool:
        """
        For some APIs, stored state may become invalid if stored too long.

        Return true if the old data should be deleted and fetched from scratch.
        """
        return False  # Default, assume checkpoints never expire

    def get_progress_timestamp(self) -> t.Optional[int]:
        """If the checkpoint can, give the time it corresponds to"""
        return None


TFetchCheckpoint = t.TypeVar("TFetchCheckpoint", bound=FetchCheckpointBase)


class SignalOpinionCategory(IntEnum):
    """
    What the opinion on a signal is.

    Some APIs may not support all of these, but each of these should influence
    what action you might take as a result of matching, otherwise it might
    make more sense as a tag
    """

    FALSE_POSITIVE = 0  # Signal generates false positives
    WORTH_INVESTIGATING = 1  # Indirect indicator
    TRUE_POSITIVE = 2  # Confirmed meets category


@dataclass
class SignalOpinion:
    """
    The metadata of a single signal upload.

    Certain APIs won't have any concept of owner, category, or tags,
    in which case owner=0, category=TRUE_POSITIVE, tags=[] is reasonable
    default.

    Some implementations may extend this to store additional API-specific data

    @see threatexchange.fetch_api.SignalExchangeAPI
    """

    owner: int
    category: SignalOpinionCategory
    tags: t.Set[str]

    @classmethod
    def get_trivial(cls):
        return cls(0, SignalOpinionCategory.WORTH_INVESTIGATING, [])


class AggregateSignalOpinionCategory(IntEnum):
    """
    Represent multiple opinions as one.

    Keep in Sync with SignalOpinionCategory
    """

    FALSE_POSITIVE = 0  # Signal generates false positives
    WORTH_INVESTIGATING = 1  # Indirect indicator
    TRUE_POSITIVE = 2  # Confirmed meets category
    DISPUTED = 3  # Some positive, some negative

    @classmethod
    def from_opinion_categories(
        cls, opinion_categories: t.Iterable[SignalOpinionCategory]
    ) -> "AggregateSignalOpinionCategory":
        aggregate_opinion = None
        for category in opinion_categories:
            aggregate_opinion = cls.aggregate(aggregate_opinion, category)
        assert aggregate_opinion is not None
        return aggregate_opinion

    @classmethod
    def aggregate(
        cls,
        old: t.Optional["AggregateSignalOpinionCategory"],
        new: t.Union["AggregateSignalOpinionCategory", SignalOpinionCategory],
    ) -> "AggregateSignalOpinionCategory":
        """
        Combine signal opinions into an aggregate opinion.

        In general, take the highest confidence/severity of true positives,
        unless you have both a true + false positive, in which case the result
        is disputed.
        """
        new = AggregateSignalOpinionCategory(new)
        if old is None:
            return new
        lo = min(old, new)
        hi = max(old, new)
        if lo == hi:
            return hi
        return cls.DISPUTED if lo == cls.FALSE_POSITIVE else hi


@dataclass
class AggregateSignalOpinion:

    category: AggregateSignalOpinionCategory
    tags: t.Set[str]

    @classmethod
    def from_opinions(cls, opinions: t.List[SignalOpinion]) -> "AggregateSignalOpinion":
        assert opinions
        return cls(
            tags={t for o in opinions for t in o.tags},
            category=AggregateSignalOpinionCategory.from_opinion_categories(
                o.category for o in opinions
            ),
        )


@dataclass
class FetchedSignalMetadata:
    """
    Metadata to make decisions on matches and power feedback on the fetch API.

    You likely need to extend this for your API to include enough context for
    SignalExchangeAPI.report_seen() and others.

    If your API supports multiple databases or collections, you likely
    will need to store that here.
    """

    def get_as_opinions(self) -> t.List[SignalOpinion]:
        return [SignalOpinion.get_trivial()]

    @classmethod
    def merge_metadata(cls: t.Type[Self], _older: Self, newer: Self) -> Self:
        """
        The merge strategy when tailing a stream of updates.

        Simple strategies might be:
        1. Replace - newer records for the same signal complete replace old ones
        2. Merge - new records are combined with old ones
        """
        return newer  # Default is replace

    def get_as_aggregate_opinion(self) -> AggregateSignalOpinion:
        return AggregateSignalOpinion.from_opinions(self.get_as_opinions())

    def __str__(self) -> str:
        agg = self.get_as_aggregate_opinion()
        if not agg.tags:
            return agg.category.name
        return f"{agg.category.name} {','.join(agg.tags)}"


TFetchedSignalMetadata = t.TypeVar(
    "TFetchedSignalMetadata", bound=FetchedSignalMetadata
)


class FetchDelta(t.Generic[TFetchCheckpoint]):
    """
    Contains the result of a fetch.

    You'll need to extend this, but it only to be interpretable by your
    API's version of FetchedState
    """

    def record_count(self) -> int:
        """Helper for --limit"""
        return 1

    def next_checkpoint(self) -> TFetchCheckpoint:
        """A serializable checkpoint for fetch."""
        raise NotImplementedError

    def has_more(self) -> bool:
        """
        Returns true if the API has no more data at this time.
        """
        raise NotImplementedError


class FetchDeltaWithUpdateStream(
    t.Generic[TFetchCheckpoint, TFetchedSignalMetadata], FetchDelta[TFetchCheckpoint]
):
    """
    For most APIs, they can represented in a simple update stream.

    This allows naive implementations for storage.
    """

    def get_as_update_dict(
        self,
    ) -> t.Mapping[t.Tuple[str, str], t.Optional[TFetchedSignalMetadata]]:
        """
        Returns the contents of the delta as
         (signal_type, signal_str) => record
        If the record is set to None, this indicates the record should be
        deleted if it exists.
        """
        raise NotImplementedError


# TODO t.Generic[TFetchDeltaBase, TFetchedSignalDataBase, FetchCheckpointBase]
#      to help keep track of the expected subclasses for an impl
class FetchedStateStoreBase:
    """
    An interface to previously fetched or persisted state.

    You will need to extend this for your API, but even worse, there
    might need to be multiple versions for a single API if it's being
    used by Hasher-Matcher-Actioner, since that might want to specialcase
    for AWS components.

    = A Note on Metadata ID =
    It's assumed that the storage will be split into a scheme that allows
    addressing individual IDs. Depending on the implementation, you may
    have to invent IDs during merge() which will also need to be persisted,
    since they need to be consistent between instanciation
    """

    def get_checkpoint(
        self, collab: CollaborationConfigBase
    ) -> t.Optional[FetchCheckpointBase]:
        """
        Returns the last checkpoint passed to merge() after a flush()
        """
        raise NotImplementedError

    def merge(self, collab: CollaborationConfigBase, delta: FetchDelta) -> None:
        """
        Merge a FetchDelta into the state.

        At the implementation's discretion, it may call flush() or the
        equivalent work.
        """
        raise NotImplementedError

    def flush(self) -> None:
        """
        Finish writing the results of previous merges to persistant state.

        This should also persist the checkpoint.
        """
        raise NotImplementedError

    def clear(self, collab: CollaborationConfigBase) -> None:
        """
        Delete all the stored state for this collaboration.
        """
        raise NotImplementedError

    def get_for_signal_type(
        self, collabs: t.List[CollaborationConfigBase], signal_type: t.Type[SignalType]
    ) -> t.Dict[str, t.Dict[str, FetchedSignalMetadata]]:
        """
        Get as a map of CollabConfigBase.name() => {signal: Metadata}

        This is meant for simple storage and indexing solutions, but at
        scale, you likely want to store as IDs rather than the full metadata.

        TODO: This currently implies that you are going to load the entire dataset
        into memory, which once we start getting huge amounts of data, might not make
        sense.
        """
        raise NotImplementedError
