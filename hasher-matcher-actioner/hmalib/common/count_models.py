# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import typing as t
from decimal import Decimal

from mypy_boto3_dynamodb.service_resource import Table
from boto3.dynamodb.conditions import Attr


class MatchByPrivacyGroupCounter:
    """
    Updates and retrieves counts of matches by Privacy Group.

    Everything is a class method so you can extend this class, override what you
    see fit and get the behavior without writing more than you need to. This
    class might in the future become a base class for all counters.
    """

    @classmethod
    def get_all_counts(cls, table: Table) -> t.Dict[str, int]:
        response = table.scan(FilterExpression=Attr("PK").eq(cls._get_pkey()))
        return {
            t.cast(str, item["SK"]).split("#", 1)[1]: int(
                t.cast(Decimal, item["WriteCount"])
            )
            for item in response["Items"]
        }

    @classmethod
    def get_count(cls, table: Table, privacy_group: str) -> int:
        response = table.get_item(
            Key={"PK": cls._get_pkey(), "SK": cls._get_skey(privacy_group)}
        )
        return (
            "Item" in response
            and int(t.cast(Decimal, response["Item"]["WriteCount"]))
            or 0
        )

    @classmethod
    def increment_counts(cls, table: Table, counts: t.Dict[str, int]):
        for pg in counts:
            table.update_item(
                # Couldn't find a way to do update_item in batch. Can optimize
                # if found.
                Key={"PK": cls._get_pkey(), "SK": cls._get_skey(pg)},
                UpdateExpression="SET WriteCount = if_not_exists(WriteCount, :zero) + :by",
                ExpressionAttributeValues={":by": counts[pg], ":zero": 0},
            )

    @classmethod
    def _get_pkey(cls) -> str:
        return "counters#match-by-privacy-group"

    @classmethod
    def _get_skey(cls, privacy_group: str) -> str:
        return f"pg#{privacy_group}"
