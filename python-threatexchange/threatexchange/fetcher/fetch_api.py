# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
The fetcher is the component that talks to external APIs to get and put signals

@see SignalExchangeAPI
"""


import typing as t

from threatexchange import common
from threatexchange.fetcher.collab_config import CollaborationConfigBase
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.fetcher import fetch_state as state

TCollabConfig = t.TypeVar("TCollabConfig", bound=CollaborationConfigBase)
TFetchDelta = t.TypeVar("TFetchDelta", bound=state.FetchDelta)

# TODO t.Generic[TFetchDelta, TFetchedSignalData, TCollabConfig]
#      In order to make it easier to track the expected extensions for an API
class SignalExchangeAPI:
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
    def get_checkpoint_cls(cls) -> t.Type[state.FetchCheckpointBase]:
        """Returns the dataclass used to control checkpoint for this API"""
        return state.FetchCheckpointBase  # Default = no checkpoints

    @classmethod
    def get_record_cls(cls) -> t.Type[state.FetchedSignalMetadata]:
        """Returns the dataclass used to store records for this API"""
        return state.FetchedSignalMetadata  # Default = no metadata

    @classmethod
    def get_config_class(cls) -> t.Type[CollaborationConfigBase]:
        """Returns the dataclass used to store records for this API"""
        return CollaborationConfigBase

    # TODO - this doens't work for StopNCII which sends the owner as a string
    #        maybe this should take the full metadata?
    def resolve_owner(self, id: int) -> str:
        """
        Convert an owner ID into a human readable name (if available).

        If empty string is returned, a placeholder will be used instead.
        """
        return ""

    def get_own_owner_id(self, collab: CollaborationConfigBase) -> int:
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

    def fetch_once(
        self,
        supported_signal_types: t.List[t.Type[SignalType]],
        collab: CollaborationConfigBase,
        # None if fetching for the first time,
        # otherwise the previous FetchDelta returned
        checkpoint: t.Optional[state.FetchCheckpointBase],
    ) -> state.FetchDelta[state.FetchCheckpointBase]:
        """
        Call out to external resources, pulling down one "batch" of content.

        Many APIs are a sequence of events: (creates/updates, deletions)
        In that case, it's important the these events are strictly ordered.
        I.e. if the sequence is create => delete, if the sequence is reversed
        to delete => create, the end result is a stored record, when the
        expected is a deleted one.
        """
        raise NotImplementedError

    def report_seen(
        self,
        collab: CollaborationConfigBase,
        s_type: SignalType,
        signal: str,
        metadata: state.FetchedStateStoreBase,
    ) -> None:
        """
        Report that you observed this signal.

        This is an optional API, and places that use it should catch
        the NotImplementError.
        """
        raise NotImplementedError

    def report_opinion(
        self,
        collab: CollaborationConfigBase,
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
        collab: CollaborationConfigBase,
        s_type: t.Type[SignalType],
        signal: str,
        metadata: state.FetchedSignalMetadata,
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
        collab: CollaborationConfigBase,
        s_type: t.Type[SignalType],
        signal: str,
        metadata: state.FetchedSignalMetadata,
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


class SignalExchangeAPIWithIterFetch(
    t.Generic[
        state.TFetchCheckpoint
    ],  # TODO move to SignalExchangeAPI in a future diff
    SignalExchangeAPI,
):
    """
    Provides an alternative fetch_once implementation to simplify state

    @see fetch_iter
    """

    def __init__(self) -> None:
        self._fetch_iters: t.Dict[
            str, t.Iterator[state.FetchDelta[state.TFetchCheckpoint]]
        ] = {}

    def fetch_once(  # type: ignore[override]  # fix with generics on base
        self,
        supported_signal_types: t.List[t.Type[SignalType]],
        collab: CollaborationConfigBase,
        # None if fetching for the first time,
        # otherwise the previous FetchDelta returned
        checkpoint: t.Optional[state.TFetchCheckpoint],
    ) -> state.FetchDelta[state.TFetchCheckpoint]:
        it = self._fetch_iters.get(collab.name)
        if it is None:
            it = self.fetch_iter(supported_signal_types, collab, checkpoint)
            self._fetch_iters[collab.name] = it
        delta = next(it, None)
        # This can happen if the last yielded element did not set done
        # which will cause next() to be called again after the iterator
        # is exhaused
        assert delta is not None, "fetch_iter stopping yielding too early"
        return delta

    def fetch_iter(
        self,
        supported_signal_types: t.List[t.Type[SignalType]],
        collab: CollaborationConfigBase,
        # None if fetching for the first time,
        # otherwise the previous FetchDelta returned
        checkpoint: t.Optional[state.TFetchCheckpoint],
    ) -> t.Iterator[state.FetchDelta[state.TFetchCheckpoint]]:
        """
        An alternative to fetch_once implementation to simplify state.

        Since we expect fetch_once to be called sequentially, we can safely
        store things like next_page takens in the implementation.

        TODO: This seems straight up better than fetch_once, refactor out
        """
        raise NotImplementedError
