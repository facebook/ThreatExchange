# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Defines metadata objects that are indexed. All hash indexes allow querying for a
hash. This hash can be of type PDQ, MD5, TLSH, etc. The index returns a list of
IndexMatch objects. Classes exposed in this module define the 'type' of the
metadata attribute of an IndexMatch object.

This allows us to ensure that all IndexMatch.metadata objects have a common
shape so we can write logic around it.
"""

import typing as t

from dataclasses import asdict, dataclass, field


class BaseIndexMetadata:
    def get_source(self) -> str:
        raise NotImplemented

    def to_json(self) -> t.Dict[str, t.Any]:
        return asdict(self)


# Note changing this value will change S3ThreatDataConfig.SOURCE_STR. Per my
# lookup, this will not affect how data gets stored, only logs, but should
# figure it out.
THREAT_EXCHANGE_SOURCE_SHORT_CODE = "te"

BANKS_SOURCE_SHORT_CODE = "bnk"


@dataclass
class ThreatExchangeIndicatorIndexMetadata(BaseIndexMetadata):
    """
    A row of data returned from ThreatExchange. Should correspond to a single
    descriptor.
    """

    # ThreatExchange Indicator ID.
    indicator_id: str

    # Actual value of the hash, use a string representation.
    signal_value: str

    # Which privacy groups report this indicator? Usually, will be a set of one,
    # but because an indicator can be in multiple privacy_groups, using a set.
    privacy_group: str

    # Tags reported by threatexchange for this privacy group. Will not contain
    # all tags, but a sub-set.
    tags: t.Set[str] = field(default_factory=set)

    def get_source(self):
        return THREAT_EXCHANGE_SOURCE_SHORT_CODE

    def to_json(self) -> t.Dict[str, t.Any]:
        result = asdict(self)
        result.update(tags=list(self.tags))
        return result


@dataclass
class BankedSignalIndexMetadata(BaseIndexMetadata):
    """
    A row of data stored as a bank member signal. A more compact view so that we
    can store along the index.
    """

    # Bank signal_id, this is roughly the same as an indicator id in
    # ThreatExchange. Separate bank_members which hash to the same signal value
    # will have the same signal_id.
    signal_id: str

    # Actual value of the hash, use a string representation.
    signal_value: str

    # Along with a signal_id, this should suffice as a uniqueness constraint.
    bank_member_id: str

    def get_source(self):
        return BANKS_SOURCE_SHORT_CODE
