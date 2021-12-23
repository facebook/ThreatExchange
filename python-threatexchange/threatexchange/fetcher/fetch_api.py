#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
The fetcher is the component that talks to external APIs to get and put signals

@see Fetcher
"""


import typing as t

from threatexchange.collab_config import CollaborationConfig
from threatexchange.signal_type.signal_base import SignalType
from . import fetch_state_base as state


class SignalExchangeAPI:
    """
    An external APIs to get and maybe put signals

    Fetchers ideally can checkpoint their progress, so that they can tail
    updates from the server.

    Is assumed that fetched signals have some metadata attached to them,
    which is unique to that API. Additionally, it a assumed that there
    might be multiple contributors to signals inside of an API.

    The Fetcher can assume it is stateful, and
    """

    @classmethod
    def name(cls) -> str:
        """
        A string name unique to all SignalExchangeAPIs

        This will get stored for lookup from a map of supported APIs
        keyed str: API
        """
        return cls.__name__

    def resolve_owner(self, id: int) -> str:
        """
        Convert an owner ID into a human readable name (if available)

        If empty is returned, its assumed that the collaboration name itself
        is good enough to describe this content.
        """
        return ""

    def get_own_owner_id(self) -> int:
        """
        Return the owner ID of this caller. Opinions with that ID are "ours"
        """
        return -1

    def fetch_once(
        self, collab: CollaborationConfig, checkpoint: t.Any
    ) -> state.FetchDelta:
        """
        Call out to external resources, pulling down one "batch" of content.
        """
        raise NotImplementedError

    def report_seen(
        self, s_type: SignalType, signal: str, metadata: state.FetchMetadata
    ) -> None:
        """Report that this signal was observed on your platform"""
        raise NotImplementedError

    def report_opinion(
        self,
        collab: CollaborationConfig,
        s_type: t.Type[SignalType],
        signal: str,
        opinion: state.SignalOpinion,
    ) -> None:
        """
        Weigh in on a signal for this collaboration.

        Most implementations will want a full replacement specialization, but this
        allows a common interface for all uploads for the simplest usecases.
        """
        raise NotImplementedError

    def report_true_positive(
        self,
        s_type: t.Type[SignalType],
        signal: str,
        metadata: state.FetchedSignalData,
    ) -> None:
        """Report that a previously seen signal was a true positive"""
        raise NotImplementedError

    def report_false_positive(
        self,
        s_type: t.Type[SignalType],
        signal: str,
        metadata: state.FetchedSignalData,
    ) -> None:
        """Report that a previously seen signal is a false positive"""
        raise NotImplementedError
