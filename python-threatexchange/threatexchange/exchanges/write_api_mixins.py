# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
These contain small mixins that enable write features on SignalExchangeAPI

While it would be possible to make all these extensions of SignalExchangeAPI,
we're just about at the limit of understandable complexity for the typing on
SignalExchangeAPI, and so moving these into mixins might allow us to simplify
the logic a bit.

Example
  class MyApiWithFeedback(
    SignalExchangeAPI[
        MyCollabConfig,
        MyCheckpoint,
        MySignalMetadata,
        str,
        MyUpdateRecordValue,
    ],
    ExchangeWithSeen[MyCollabConfig, MyUpdateRecordValue],
    ExchangeWithFeedback[MyCollabConfig, MyUpdateRecordValue],
    ExchangeWithUpload[MyCollabConfig],
    ):
      pass

  # Inside py-tx reflection
  if isinstance(exchange, ExchangeWithSeen):
    exchange.submit_matched(collab, metadata)


@see SignalExchangeAPI
"""

import typing as t

from threatexchange.exchanges import fetch_state
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.exchanges.collab_config import CollaborationConfigBase


TCollabConfig = t.TypeVar("TCollabConfig", bound=CollaborationConfigBase)
TFetchedSignalMetadata = t.TypeVar(
    "TFetchedSignalMetadata", bound=fetch_state.FetchedSignalMetadata
)


class ExchangeWithMatchedOnPlatform(
    t.Generic[TCollabConfig, fetch_state.TUpdateRecordKey]
):
    """
    Mixin for an exchange that supports recording you have successfully made a match

    This can be useful for automatically cerifying that your matching pipeline is
    functioning, or to allow insights on platform spread.
    """

    def submit_matched(
        self,
        # The collaboration we should share the event to
        collab: TCollabConfig,
        # The API record that we matched, corresponding to the key
        # from the original API. This seems to be unifying across all existing APIs
        # though some can reconstruct the feedback target from the signal or the metadata
        matched_record_key: fetch_state.TUpdateRecordKey,
    ) -> None:
        """
        Report that you matched this signal to content on your platform.

        This doesn't have any indication of whether this content is harmful,
        but this can help certify that your matching implementation is
        functional, and help other platforms track platform-to-platform
        spread.
        """
        raise NotImplementedError


class ExchangeWithReviewFeedback(
    t.Generic[TCollabConfig, fetch_state.TUpdateRecordKey]
):
    """
    Mixin for exchanges that supports recording the results of a manual review.

    This can help other platforms stack rank potential matches for review to
    prioritize the ones that seem to work well accross multiple platforms.
    """

    def submit_review_feedback(
        self,
        # The collaboration we should share the event to
        collab: TCollabConfig,
        # The API record that we're sharing feedback on, corresponding to the key
        # from the original API. This seems to be unifying across all existing APIs
        # though some can reconstruct the feedback target from the signal or the metadata
        matched_record_key: fetch_state.TUpdateRecordKey,
        # Whether the review of matched content corresponded to material the
        # exchange aims to find. Usually this corresponds to harmful content
        review_result: t.Literal[
            fetch_state.SignalOpinionCategory.POSITIVE_CLASS,
            fetch_state.SignalOpinionCategory.NEGATIVE_CLASS,
        ],
        # Someday, we might also support tags, since StopNCII supports it
        # tags: t.Optional[t.Set[str]] = None
    ) -> None:
        """
        Report that you matched this signal to content on your platform.

        This doesn't have any indication of whether this content is harmful,
        but this can help certify that your matching implementation is
        functional, and help other platforms track platform-to-platform
        spread.
        """
        raise NotImplementedError


class ExchangeWithUpload(t.Generic[TCollabConfig]):
    """
    Mixin for exchanges that supports uploading new opinions to the exchange
    """

    def submit_opinion(
        self,
        # The collaboration we should upload the opinion to
        collab: TCollabConfig,
        # The SignalType we are uploading
        s_type: t.Type[SignalType],
        # The signal value we are uploading
        signal: str,
        # The opinion we are sharing
        opinion: fetch_state.SignalOpinion,
    ) -> None:
        """
        Weigh in on a signal for this collaboration.

        Most implementations will want a full replacement specialization, but this
        allows a common interface for all uploads for the simplest usecases.
        """
        raise NotImplementedError
