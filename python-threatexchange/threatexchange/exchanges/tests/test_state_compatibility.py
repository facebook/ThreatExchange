# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Tests for compatibility changes between versions.

Currently this assumes pickle compatibility - we don't have an answer for
dataclass changes yet.

When changing classes (adding non-default fields, renaming fields), copy
paste the old definition into one of the testcases below.

In the test cases, the class descriptions will be used for context, so
include:
  1. The last version it was available
  2. The change

i.e.
    @dataclass
    class SignalOpinionOwnerRemoved:
        '''
        0.99.x => 1.0.0

        owner: int => is_mine: bool
        '''
        owner: int
        category: SignalOpinionCategory
        tags: t.Set[str]
"""

import copy
from dataclasses import dataclass, field
import pickle
import typing as t

import pytest

from threatexchange.exchanges.fetch_state import (
    FetchCheckpointBase,
    SignalOpinion,
    SignalOpinionCategory,
)
from threatexchange.exchanges.impl.fb_threatexchange_api import FBThreatExchangeOpinion
from threatexchange.exchanges.impl.ncmec_api import NCMECCheckpoint, NCMECOpinion


def get_SignalOpinion() -> t.Tuple[SignalOpinion, t.Sequence[object]]:
    ## Current
    is_mine = False
    category = SignalOpinionCategory.POSITIVE_CLASS
    tags = {"a", "c"}

    # 1.0.x
    current = SignalOpinion(is_mine=is_mine, category=category, tags=tags)

    # 0.99.x
    @dataclass
    class SignalOpinionOwnerRemoved:
        """
        0.99.x => 1.0.0

        owner: int => is_mine: bool (False)
        """

        owner: int
        category: SignalOpinionCategory
        tags: t.Set[str]

    owner_removed = SignalOpinionOwnerRemoved(owner=501, category=category, tags=tags)

    return (current, [owner_removed])


def get_FBThreatExchangeOpinion() -> (
    t.Tuple[FBThreatExchangeOpinion, t.Sequence[object]]
):
    ## Current
    is_mine = False
    category = SignalOpinionCategory.POSITIVE_CLASS
    tags = {"a", "c"}
    owner_app_id = 502
    descriptor_id = 1001

    # 1.0.x
    current = FBThreatExchangeOpinion(
        is_mine=is_mine,
        category=category,
        tags=tags,
        descriptor_id=descriptor_id,
        owner_app_id=owner_app_id,
    )

    # 0.99.x
    @dataclass
    class FBThreatExchangeOpinionOwnerMoved:
        """
        0.99.x => 1.0.0

        owner: int => is_mine: bool (False)
        """

        owner: int
        category: SignalOpinionCategory
        tags: t.Set[str]
        descriptor_id: int

    owner_moved = FBThreatExchangeOpinionOwnerMoved(
        owner=owner_app_id, category=category, tags=tags, descriptor_id=descriptor_id
    )

    return (current, [owner_moved])


def get_NCMECOpinion() -> t.Tuple[NCMECOpinion, t.Sequence[object]]:
    ## Current
    is_mine = False
    category = SignalOpinionCategory.POSITIVE_CLASS
    tags = {"a", "c"}
    esp_id = 602

    # 1.0.x
    current = NCMECOpinion(
        is_mine=is_mine,
        category=category,
        tags=tags,
        esp_id=esp_id,
    )

    # 0.99.x
    @dataclass
    class NCMECOpinionOwnerMoved:
        """
        0.99.x => 1.0.0

        owner: int => esp_id, is_mine: bool (False)
        """

        owner: int
        category: SignalOpinionCategory
        tags: t.Set[str]

    owner_moved = NCMECOpinionOwnerMoved(owner=esp_id, category=category, tags=tags)

    return (current, [owner_moved])


def get_NCMECCheckpoint() -> t.Tuple[NCMECCheckpoint, t.Sequence[object]]:
    ## Current
    max_ts = 1197433091

    # 1.0.x
    current = NCMECCheckpoint(get_entries_max_ts=max_ts, next="", last_fetch_time=0)

    # 0.99.x
    @dataclass
    class NCMECCheckpointTsMoved(FetchCheckpointBase):
        """
        0.99.x => 1.0.0

        max_timestamp: int => get_entries_max_ts
        """

        max_timestamp: int

    ts_moved = NCMECCheckpointTsMoved(max_timestamp=max_ts)

    return (current, [ts_moved])


@pytest.mark.parametrize(
    ("current_version", "historical_versions"),
    [
        get_SignalOpinion(),
        get_FBThreatExchangeOpinion(),
        get_NCMECOpinion(),
        get_NCMECCheckpoint(),
    ],
)
def test_previous_pickle_state(
    current_version: object, historical_versions: t.Sequence[object]
):
    # Sanity
    serialized = pickle.dumps(current_version)
    assert (
        pickle.loads(serialized) == current_version
    ), "Current object serialization not sane"

    for historical in historical_versions:
        # This isn't a perfect simulation of this works, but it's the best we have
        clone_for_pickle = copy.deepcopy(historical)
        # These will trick the pickle serializer to unserialize it as the new class
        clone_for_pickle.__class__ = current_version.__class__
        clone_for_pickle.__module__ = current_version.__module__
        serialized = pickle.dumps(clone_for_pickle)
        unserialized = pickle.loads(serialized)
        assert (
            unserialized == current_version
        ), f"Historical serialization failed: {historical.__class__.__doc__}"
