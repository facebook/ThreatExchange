#!/usr/bin/env python

"""
Wrappers for the json returned by the ThreatExchange API to typed objects.
"""

import typing as t


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
        return not self.is_false_positive

    @property
    def is_false_positive(self) -> bool:
        return self.status == "NON_MALICIOUS"


class SimpleDescriptorRollup:
    """
    A simple way to merge opinions on the same indicator.

    This contains all the information needed for simple SignalType state.
    """

    __slots__ = ["first_descriptor_id", "added_on", "labels"]

    def __init__(
        self, first_descriptor_id: int, added_on: str, labels: t.Set[str]
    ) -> None:
        self.first_descriptor_id = first_descriptor_id
        self.added_on = added_on  # TODO - convert to int?
        self.labels = set(labels)

    def merge(self, descriptor: ThreatDescriptor) -> None:
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
