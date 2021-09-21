# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Coordinates common operations on banks. Conceptually midway between the API and
the DB Layer. 
"""
import typing as t

from threatexchange.content_type.content_base import ContentType

from hmalib.common.models.bank import BankMember, BanksTable


def add_bank_member(
    banks_table: BanksTable,
    bank_id: str,
    content_type: t.Type[ContentType],
    storage_bucket: t.Optional[str],
    storage_key: t.Optional[str],
    raw_content: t.Optional[str],
    notes: str,
) -> BankMember:
    """
    WIP: As of now, just writes the bank member to the database. Once
    functionality for signal extraction, adding-to-index is written, this should
    be the callsite.
    """
    return banks_table.add_bank_member(
        bank_id=bank_id,
        content_type=content_type,
        storage_bucket=storage_bucket,
        storage_key=storage_key,
        raw_content=raw_content,
        notes=notes,
    )
