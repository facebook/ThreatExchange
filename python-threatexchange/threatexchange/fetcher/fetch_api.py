# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
The fetcher is the component that talks to external APIs to get and put signals

@see SignalExchangeAPI
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import typing as t

from threatexchange import common
from threatexchange.fetcher.collab_config import CollaborationConfigBase
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.fetcher import fetch_state as state

TCollabConfig = t.TypeVar("TCollabConfig", bound=CollaborationConfigBase)


class SignalExchangeAPI(
    t.Generic[
        TCollabConfig,
        state.TFetchCheckpoint,
        state.TFetchedSignalMetadata,
        state.TUpdateRecord,
    ],
    ABC,
):
    """
    APIs to get and maybe put signals.

    Fetchers ideally can checkpoint their progress, so that they can tail
    updates.

    While this interface is primarily intended for connecting with
    externally hosted servers, it might be useful to write adopters for
    certain formats of local files, which could be valuable for testing.

    Is assumed that fetched signals have some metadata attached to them,
    which is unique to that API. Additionally, it a assumed that there
    might be multiple contributors (owners) to signals inside of an API.

    An instance of this class can retain state (caching connecting, etc)
    as needed.

    Methods with an implementation are optional, but may rely on

    = On Owner IDs =
    Some APIs may not have any concept of owner ID (because the owner is the
    API itself). In that case, it's suggested to use 0 for all IDs. If the you
    own the API, it may also make sense to have 0 be the return of
    get_own_owner_id, which is used by matching to tell if a signal be
    considered "confirmed" or not. If your API does support the concept of
    owners, make sure to implement resolve_owner and get_own_owner_id

    """

    @classmethod
    def get_name(cls) -> str:
        """
        A simple string name unique to SignalExchangeAPIs in use.

        It should be one lowercase_with_underscores word.

        This shouldn't be changed once comitted, or you may break naive
        storage solutions (like the one in the CLI) which stores fetched
        data by (SignalExchangeAPI.name(), collab_name).
        """
        name = cls.__name__
        for suffix in ("API", "Exchange"):
            if name.endswith(suffix):
                name = name[: -len(suffix)]
        return common.class_name_to_human_name(name, "Signal")

    @classmethod
    def get_checkpoint_cls(cls) -> t.Type[state.TFetchCheckpoint]:
        """Returns the dataclass used to control checkpoint for this API"""
        # Default = no checkpoints
        return state.FetchCheckpointBase  # type: ignore

    @classmethod
    def get_record_cls(cls) -> t.Type[state.TFetchedSignalMetadata]:
        """Returns the dataclass used to store records for this API"""
        # Default = no metadata
        return state.FetchedSignalMetadata  # type: ignore

    @classmethod
    def get_config_class(cls) -> t.Type[TCollabConfig]:
        """Returns the dataclass used to store records for this API"""
        # Default - just knowing the type is enough
        return CollaborationConfigBase  # type: ignore

    @classmethod
    @abstractmethod
    def naive_fetch_merge(
        cls,
        old: t.Optional[state.TUpdateRecord],
        new: state.TUpdateRecord,
    ) -> state.TUpdateRecord:
        """
        Merge a new update produced by fetch in-memory.

        It is safe to merge into `old` in-place if supported, and return that.

        This is the fallback method of creating state when there isn't a
        specialized storage for the fetch type.

        For example, if you have nothing else, merging NCMEC update records
        together by ID will eventually get you an entire copy of the database.
        However, if it started to get too big where it would be a problem to
        load into memory, it would be better to store in a storage that
        only let you update the IDs you had updates for, or let you build an
        index based on other fields inside. If you were doing that, you
        wouldn't use this and rely on a specialzied implementation for this
        API that extends FetchStateStore.
        """
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def naive_convert_to_signal_type(
        cls,
        signal_types: t.Sequence[t.Type[SignalType]],
        fetched: state.TUpdateRecord,
    ) -> t.Dict[t.Type[SignalType], t.Dict[str, state.TFetchedSignalMetadata]]:
        """
        Convert the record from the API format to the format needed for indexing.

        This is the fallback method of creating state when there isn't a
        specialized storage for the fetch type.

        """
        raise NotImplementedError

    # TODO - this doens't work for StopNCII which sends the owner as a string
    #        maybe this should take the full metadata?
    def resolve_owner(self, id: int) -> str:
        """
        Convert an owner ID into a human readable name (if available).

        If empty string is returned, a placeholder will be used instead.
        """
        return ""

    def get_own_owner_id(self, collab: TCollabConfig) -> int:
        """
        Return the owner ID of this caller. Opinions with that ID are "ours".

        SignalOpinions returned by fetch() where the owner id is
        the return of get_own_owner_id() are assumed to be owned by you, which
        can result in some additional metadata being added to matches, for
        example in the `match` command of the CLI.

        A default implementation is provided that is assumed to not match any
        real owner ID.
        """
        return -1

    @abstractmethod
    def fetch_iter(
        self,
        supported_signal_types: t.Sequence[t.Type[SignalType]],
        collab: TCollabConfig,
        # None if fetching for the first time,
        # otherwise the previous FetchDelta returned
        checkpoint: t.Optional[state.TFetchCheckpoint],
    ) -> t.Iterator[state.FetchDelta[state.TUpdateRecord, state.TFetchCheckpoint]]:
        """
        Call out to external resources, fetching a batch of updates per yield.

        Many APIs are a sequence of events: (creates/updates, deletions)
        In that case, it's important the these events are strictly ordered.
        I.e. if the sequence is create => delete, if the sequence is reversed
        to delete => create, the end result is a stored record, when the
        expected is a deleted one.

        The iterator may be abandoned before it is completely exhausted.

        If the iterator returns, it should be because there is no more data
        (i.e. the fetch is up to date).
        """
        raise NotImplementedError

    def report_seen(
        self,
        collab: TCollabConfig,
        s_type: SignalType,
        signal: str,
        metadata: state.TFetchedSignalMetadata,
    ) -> None:
        """
        Report that you observed this signal.

        This is an optional API, and places that use it should catch
        the NotImplementError.
        """
        raise NotImplementedError

    def report_opinion(
        self,
        collab: TCollabConfig,
        s_type: t.Type[SignalType],
        signal: str,
        opinion: state.SignalOpinion,
    ) -> None:
        """
        Weigh in on a signal for this collaboration.

        Most implementations will want a full replacement specialization, but this
        allows a common interface for all uploads for the simplest usecases.

        This is an optional API, and places that use it should catch
        the NotImplementError.
        """
        raise NotImplementedError

    def report_true_positive(
        self,
        collab: TCollabConfig,
        s_type: t.Type[SignalType],
        signal: str,
        metadata: state.TFetchedSignalMetadata,
    ) -> None:
        """
        Report that a previously seen signal was a true positive.

        This is an optional API, and places that use it should catch
        the NotImplementError.
        """
        self.report_opinion(
            collab,
            s_type,
            signal,
            state.SignalOpinion(
                owner=self.get_own_owner_id(collab),
                category=state.SignalOpinionCategory.TRUE_POSITIVE,
                tags=set(),
            ),
        )

    def report_false_positive(
        self,
        collab: TCollabConfig,
        s_type: t.Type[SignalType],
        signal: str,
        metadata: state.TFetchedSignalMetadata,
    ) -> None:
        """
        Report that a previously seen signal is a false positive.

        This is an optional API, and places that use it should catch
        the NotImplementError.
        """
        self.report_opinion(
            collab,
            s_type,
            signal,
            state.SignalOpinion(
                owner=self.get_own_owner_id(collab),
                category=state.SignalOpinionCategory.FALSE_POSITIVE,
                tags=set(),
            ),
        )


# A convenience helper since mypy can't intuit that bound != t.Any
# For methods like get_checkpoint_cls
TSignalExchangeAPI = SignalExchangeAPI[
    CollaborationConfigBase,
    state.FetchCheckpointBase,
    state.FetchedSignalMetadata,
    t.Any,
]

TSignalExchangeAPICls = t.Type[TSignalExchangeAPI]


K = t.TypeVar("K")
V = t.TypeVar("V")


class SignalExchangeAPIWithKeyedUpdates(
    SignalExchangeAPI[
        TCollabConfig,
        state.TFetchCheckpoint,
        state.TFetchedSignalMetadata,
        t.Dict[K, t.Optional[V]],
    ]
):
    """
    An API that supports sequential updates with a common key (id, hash, etc).

    This provides a simple approach for merging data.
    A value of None for a value indicates that the record was deleted.
    """

    @classmethod
    def naive_fetch_merge(
        cls, old: t.Optional[t.Dict[K, t.Optional[V]]], new: t.Dict[K, t.Optional[V]]
    ) -> t.Dict[K, t.Optional[V]]:
        old = old or {}
        for k, v in new.items():
            if v is None:
                old.pop(k, None)
            else:
                old[k] = v
        return old


class SignalExchangeAPIWithSimpleUpdates(
    SignalExchangeAPIWithKeyedUpdates[
        TCollabConfig,
        state.TFetchCheckpoint,
        state.TFetchedSignalMetadata,
        t.Tuple[str, str],
        state.TFetchedSignalMetadata,
    ]
):
    """
    An API that conveniently maps directly into the form needed by index.

    If the API supports returning exactly the hashes and all the metadata needed
    to make a decision on the hash without needing an indirection of ID (for example,
    to support deletes), then you can choose to directly return it in a form that
    maps directly into SignalType.
    """

    @classmethod
    def naive_convert_to_signal_type(
        cls,
        signal_types: t.Sequence[t.Type[SignalType]],
        fetched: t.Dict[t.Tuple[str, str], t.Optional[state.TFetchedSignalMetadata]],
    ) -> t.Dict[t.Type[SignalType], t.Dict[str, state.TFetchedSignalMetadata]]:
        ret: t.Dict[t.Type[SignalType], t.Dict[str, state.TFetchedSignalMetadata]] = {}
        type_by_name = {st.get_name(): st for st in signal_types}
        for (type_str, signal_str), metadata in fetched.items():
            s_type = type_by_name.get(type_str)
            if s_type is None or metadata is None:
                continue
            inner = ret.get(s_type)
            if inner is None:
                inner = {}
                ret[s_type] = inner
            inner[signal_str] = metadata
        return ret
