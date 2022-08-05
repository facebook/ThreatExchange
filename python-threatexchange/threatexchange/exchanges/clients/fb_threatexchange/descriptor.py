# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

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

    # TODO - do something smarter than this - static
    #        class variable problematic, currently set in main.py
    MY_APP_ID = -1  # type: ignore

    # You declared the indicator was in the collaboration label set
    TRUE_POSITIVE = "true_positive"  # type: ignore
    # You declared the indicator was not in the collaboration label set
    FALSE_POSITIVE = "false_positive"  # type: ignore
    # Someone declared the indicator was not in the collaboration label set
    DISPUTED = "disputed"  # type: ignore

    # Special tags to mark whether you (or someone else)
    # has weighed in on the indicator
    SPECIAL_TAGS = frozenset((TRUE_POSITIVE, FALSE_POSITIVE, DISPUTED))  # type: ignore

    id: int
    raw_indicator: str
    indicator_type: str
    owner_id: int
    tags: t.List[str]
    status: str
    added_on: str

    @classmethod
    def from_te_json(cls, my_app_id: t.Union[str, int], td_json) -> "ThreatDescriptor":
        # Hack for now, but nearly refactored out of cls state
        cls.MY_APP_ID = my_app_id
        owner_id_str = td_json["owner"]["id"]
        tags = td_json.get("tags", [])
        # This is needed because ThreatExchangeAPI.get_threat_descriptors()
        # does a transform, but other locations do not
        if isinstance(tags, dict):
            tags = sorted(tag["text"] for tag in tags["data"])
        td = cls(  # type: ignore
            id=int(td_json["id"]),
            raw_indicator=td_json["raw_indicator"],
            indicator_type=td_json["type"],
            owner_id=int(owner_id_str),
            tags=[tag for tag in tags if tag not in ThreatDescriptor.SPECIAL_TAGS],
            status=td_json["status"],
            added_on=td_json["added_on"],
        )
        # Add special tags
        # TODO - Consider stripping out collab labels
        #        from FALSE_POSITIVE & NON_MALICIOUS
        # Is this my descriptor?
        if td.is_mine:
            if td.status == "NON_MALICIOUS":
                td.tags.append(ThreatDescriptor.FALSE_POSITIVE)
            else:
                td.tags.append(ThreatDescriptor.TRUE_POSITIVE)
        # Disputed path #1 - mark as non_malicious
        elif td.status == "NON_MALICIOUS":
            td.tags.append(ThreatDescriptor.DISPUTED)
        # Disputed path #2 - react with DISAGREE_WITH_TAGS
        elif "DISAGREE_WITH_TAGS" in td_json.get("my_reactions", ()):
            td.tags.append(ThreatDescriptor.FALSE_POSITIVE)
        elif any(
            t == "DISAGREE_WITH_TAGS" for r in td_json.get("reactions", []) for t in r
        ):
            td.tags.append(ThreatDescriptor.DISPUTED)
        return td

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
        return self.MY_APP_ID == self.owner_id


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
        return cls(descriptor.id, descriptor.added_on, set(descriptor.tags))

    @classmethod
    def from_descriptors(
        cls, descriptors: t.Iterable[ThreatDescriptor]
    ) -> "SimpleDescriptorRollup":
        ret = None
        for d in descriptors:
            if not ret:
                ret = cls.from_descriptor(d)
            else:
                ret.merge(d)
        if ret:
            return ret
        raise ValueError("Empty descriptor list!")

    def merge(self, descriptor: ThreatDescriptor) -> None:
        # Is the other descriptor mine? If so, unconditionally take it and clear
        # everything else
        if descriptor.is_mine:
            self.added_on = self.IS_MY_OPINION
            self.first_descriptor_id = descriptor.id
            self.labels = set(descriptor.tags)
            return
        # My descriptor beats my reactions, and I don't want
        # to take anyone else's opinion
        elif self.added_on == self.IS_MY_OPINION:
            return
        # Is my reaction?
        elif descriptor.is_false_positive:
            self.added_on = self.IS_MY_OPINION
            self.first_descriptor_id = descriptor.id
            self.labels = set(descriptor.tags)
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
    def from_row(cls, row: t.List[str]) -> "SimpleDescriptorRollup":
        """Simple conversion from CSV row"""
        labels = []
        if row[2]:
            labels = row[2].split(" ")
        return cls(int(row[0]), row[1], set(labels))

    @classmethod
    def from_threat_updates_json(
        cls, my_app_id: int, te_json: t.Dict[str, t.Any]
    ) -> t.Optional["SimpleDescriptorRollup"]:
        if te_json["should_delete"]:
            return None
        # https://github.com/facebook/ThreatExchange/issues/834
        if not te_json.get("descriptors", {}).get("data"):
            return None
        descriptors = []
        for descriptor_json in te_json["descriptors"]["data"]:
            # Look at me ma! I'm modifying input paramaters!
            descriptor_json["raw_indicator"] = te_json["indicator"]
            descriptor_json["type"] = te_json["type"]
            descriptors.append(
                ThreatDescriptor.from_te_json(my_app_id, descriptor_json)
            )
        return cls.from_descriptors(descriptors)

    @staticmethod
    def te_threat_updates_fields() -> t.Tuple[str, ...]:
        return (
            "id",
            "indicator",
            "type",
            "last_updated",
            "should_delete",
            "descriptors{%s}"
            % ",".join(
                (
                    "reactions",
                    "my_reactions",
                    "owner{id}",
                    "tags",
                    "status",
                    "added_on",
                )
            ),
        )
