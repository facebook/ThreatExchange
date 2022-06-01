# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
The fetcher is the component that talks to external APIs to get and put signals

@see SignalExchangeAPI
"""

from abc import ABC, abstractmethod
import typing as t

from threatexchange import common
from threatexchange.fetcher.collab_config import CollaborationConfigBase
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.fetcher import fetch_state as state

TCollabConfig = t.TypeVar("TCollabConfig", bound=CollaborationConfigBase)
TFetchDelta = t.TypeVar("TFetchDelta", bound=state.FetchDelta)


class SignalExchangeAPI(
    t.Generic[
        TCollabConfig, state.TFetchCheckpoint, state.TFetchedSignalMetadata, TFetchDelta
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

    # TODO - this doesn't work for StopNCII which sends the owner as a string
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
    ) -> t.Iterator[TFetchDelta]:
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
    state.FetchDelta[state.FetchCheckpointBase, state.FetchedSignalMetadata],
]

TSignalExchangeAPICls = t.Type[TSignalExchangeAPI]
