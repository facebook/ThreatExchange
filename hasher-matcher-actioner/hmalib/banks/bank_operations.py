# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Defines the "Banks" API. What operations can be done on a bank?

Coordinates common operations. Conceptually midway between the API and the DB
Layer. 
"""
import typing as t
import json

from mypy_boto3_sqs.client import SQSClient

from threatexchange.content_type.content_base import ContentType
from threatexchange.signal_type.signal_base import SignalType

from hmalib.lambdas.api.submit import create_presigned_url
from hmalib.common.models import content
from hmalib.common.messages.bank import BankSubmissionMessage
from hmalib.common.models.bank import BankMember, BankMemberSignal, BanksTable


def add_bank_member(
    banks_table: BanksTable,
    sqs_client: SQSClient,
    submissions_queue_url: str,
    bank_id: str,
    content_type: t.Type[ContentType],
    storage_bucket: t.Optional[str],
    storage_key: t.Optional[str],
    raw_content: t.Optional[str],
    notes: str,
) -> BankMember:
    """
    Write bank-member to database. Send a message to hashing lambda to extract signals.
    """
    member = banks_table.add_bank_member(
        bank_id=bank_id,
        content_type=content_type,
        storage_bucket=storage_bucket,
        storage_key=storage_key,
        raw_content=raw_content,
        notes=notes,
    )

    submission_message = BankSubmissionMessage(
        content_type=content_type,
        url=create_presigned_url(storage_bucket, storage_key, None, 3600, "get_object"),
        bank_id=bank_id,
        bank_member_id=member.bank_member_id,
    )
    sqs_client.send_message(
        QueueUrl=submissions_queue_url,
        MessageBody=json.dumps(submission_message.to_sqs_message()),
    )

    return member


def add_bank_member_signal(
    banks_table: BanksTable,
    bank_id: str,
    bank_member_id: str,
    signal_type: t.Type[SignalType],
    signal_value: str,
) -> BankMemberSignal:
    """
    Add a bank member signal. Will deduplicate a signal_value + signal_type
    tuple before writing to the database.

    Calling this API also makes the signal (new or existing) available to
    process into matching indices.
    """
    return banks_table.add_bank_member_signal(
        bank_id=bank_id,
        bank_member_id=bank_member_id,
        signal_type=signal_type,
        signal_value=signal_value,
    )
