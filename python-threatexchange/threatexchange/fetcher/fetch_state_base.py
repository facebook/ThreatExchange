# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Base classes for passing data between SignalExchangeAPIs and other interfaces.

Many implementations will choose to extend these to add additional metadata
needed to power API features.
"""


from dataclasses import dataclass
from enum import Enum
import typing as t

from threatexchange.signal_type.signal_base import SignalType


TFetchStateCheckpoint = t.TypeVar("TFetchStateCheckpoint")  # TODO for now


class SignalOpinionCategory(Enum):
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
    tags: t.List[str]


@dataclass
class FetchedSignalData:
    """
    Metadata to make decisions on matches and power feedback on the fetch API.

    You likely need to extend this for your API to include enough context for
    SignalExchangeAPI.report_seen() and others.

    If your API supports multiple databases or collections, you likely
    will need to store that here.
    """

    opinions: t.List[SignalOpinion]


class FetchDelta:
    """
    Contains the result of a fetch.

    You'll need to extend this, but it only to be interpretable by your
    API's version of FetchedState
    """

    def record_count(self) -> int:
        """Helper for --limit"""
        return 1

    def next_checkpoint(self) -> TFetchStateCheckpoint:
        """A serializable checkpoint for fetch."""
        raise NotImplementedError


# TODO t.Generic[TFetchDelta, TFetchedSignalData]
#      to help keep track of the expected subclasses for an impl
class FetchedState:
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

    def get_checkpoint(self) -> TFetchStateCheckpoint:
        """
        Returns the last checkpoint passed to merge() after a flush()
        """
        raise NotImplementedError

    def merge(self, delta: FetchDelta) -> None:
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

    # TODO - if sticking with this signature, convert to t.NamedTuple
    def get_as_signals(self) -> t.Dict[str, t.List[t.Tuple[str, int]]]:
        """
        Get as a map of SignalType.name() => (signal, MetataData ID).

        If the underlying API doesn't support IDs, one solution

        It's assumed that signal is unique (all merging has already taken place).

        TODO this currently implies that you are going to load the entire dataset
        into memory, which once we start getting huge amounts of data, might not make
        sense.
        """
        raise NotImplementedError

    def get_metadata_from_id(self, metadata_id: int) -> FetchedSignalData:
        """
        Fetch the metadata from an ID
        """
        raise NotImplementedError
