#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Wrappers for the json returned by the ThreatExchange API to typed objects.
"""

import collections
import typing as t

from . import TE


class ThreatDescriptor(t.NamedTuple):
    """
    Wrapper around ThreatExchange JSON for a ThreatDescriptor.

    Example:
    {
        "id": "3058061737574159"
        "raw_indicator": "facefacefacefacefacefacefaceface",
        "type": "HASH_MD5",
        "owner": {
            "id": "616912251743987",
            ...,
        },
        "status": "MALICIOUS",
        "tags": null,
        "added_on": "2020-07-01T18:31:15+0000"
        ...
    }
    """

    # You declared the indicator was in the collaboration label set
    TRUE_POSITIVE = "true_positive"
    # You declared the indicator was not in the collaboration label set
    FALSE_POSITIVE = "false_positive"
    # Someone declared the indicator was not in the collaboration label set
    DISPUTED = "disputed"

    # Special tags to mark whether you (or someone else)
    # has weighed in on the indicator
    SPECIAL_TAGS = frozenset((TRUE_POSITIVE, FALSE_POSITIVE, DISPUTED))

    id: int
    raw_indicator: str
    indicator_type: str
    owner_id: int
    tags: t.List[str]
    status: str
    added_on: str

    def to_params(self) -> t.Dict[str, t.Any]:
        params = dict(self.__dict__)
        params["type"] = params.pop("indicator_type")
        if not params["tags"]:
            del params["tags"]
        return params

    @property
    def is_true_positive(self) -> bool:
        return self.TRUE_POSITIVE in self.tags

    @property
    def is_false_positive(self) -> bool:
        return self.FALSE_POSITIVE in self.tags

    @property
    def is_mine(self) -> bool:
        """This Descriptor is my App's Opinion"""
        # TODO - come up with a way to do this that doesn't use class state
        return TE.Net.APP_TOKEN.partition("|")[0] == str(self.owner_id)


class SimpleDescriptorRollup:
    """
    A simple way to merge opinions on the same indicator.

    This contains all the information needed for simple SignalType state.
    """

    IS_MY_OPINION = "mine"

    __slots__ = ["first_descriptor_id", "added_on", "labels"]

    def __init__(
        self, first_descriptor_id: int, added_on: str, labels: t.Set[str]
    ) -> None:
        self.first_descriptor_id = first_descriptor_id
        self.added_on = added_on  # TODO - convert to int?
        self.labels = set(labels)

    @classmethod
    def from_descriptor(cls, descriptor: ThreatDescriptor) -> "SimpleDescriptorRollup":
        return cls(descriptor.id, descriptor.added_on, descriptor.tags)

    def merge(self, descriptor: ThreatDescriptor) -> None:
        # Is the other descriptor mine? If so, unconditionally take it and clear
        # everything else
        if descriptor.is_mine:
            self.added_on = self.IS_MY_OPINION
            self.first_descriptor_id = descriptor.id
            self.labels = descriptor.tags
            return
        # My descriptor beats my reactions, and I don't want
        # to take anyone else's opinion
        elif self.added_on == self.IS_MY_OPINION:
            return
        # Is my reaction?
        elif descriptor.is_false_positive:
            self.added_on = self.IS_MY_OPINION
            self.first_descriptor_id = descriptor.id
            self.labels = descriptor.tags
            return
        # Else merge the labels together
        self.added_on, self.first_descriptor_id = min(
            (self.added_on, self.first_descriptor_id),
            (descriptor.added_on, descriptor.id),
        )
        self.labels.union(descriptor.tags)

    def as_row(self) -> t.Tuple[int, str, str]:
        """Simple conversion to CSV row"""
        return self.first_descriptor_id, self.added_on, " ".join(self.labels)

    @classmethod
    def from_row(cls, row: t.Iterable) -> "SimpleDescriptorRollup":
        """Simple conversion from CSV row"""
        labels = []
        if row[2]:
            labels = row[2].split(" ")
        return cls(int(row[0]), row[1], labels)
