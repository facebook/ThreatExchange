#!/usr/bin/env python3
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
    """

    owner: int
    category: SignalOpinionCategory
    tags: t.List[str]


@dataclass
class FetchedSignalData:
    """
    Metadata to make decisions on matches and power feedback on the fetch API.
    """

    collab_name: str  # Corresponds to the collab config that fetched it
    opinions: t.List[SignalOpinion]


class FetchDelta:
    """
    Contains the result of a fetch.

    Needs only to be interpretable by FetchedState
    """

    def record_count(self) -> int:
        """Helper for --limit"""
        return 1

    def next_checkpoint(self) -> TFetchStateCheckpoint:
        """
        A serializable checkpoint for fetch
        """
        raise NotImplementedError


class FetchedState:
    """
    An interface to previously fetched or persisted state.
    """

    def get_checkpoint(self) -> TFetchStateCheckpoint:
        """
        Returns the last checkpoint passed to merge() after a flush()
        """
        raise NotImplementedError

    def merge(self, subsequent: FetchDelta) -> None:
        """
        Merge a subsequent FetchDelta into this one.

        At the implementation's discretion, it may call flush() or the
        equivalent work.
        """
        raise NotImplementedError

    def flush(self) -> None:
        """
        Finish writing the results of previous merges to persistant state.

        This should also persist the checkpoint.
        """
        return None

    def get_as_signals(self) -> t.Dict[t.Type[SignalType], t.List[t.Tuple[str, str]]]:
        """
        Get as a map of SignalType.name() => (signal, MetataData ID).

        It's assumed that signal is unique (all merging has already taken place).

        Note - this currently implies that you are going to load the entire dataset
        into memory, which once we start getting huge amounts of data, might not make
        sense.
        """
        raise NotImplementedError

    def get_metadata_from_id(self, metadata_id: int) -> FetchedSignalData:
        """
        Returns additional metadata from a match
        """
        raise NotImplementedError
