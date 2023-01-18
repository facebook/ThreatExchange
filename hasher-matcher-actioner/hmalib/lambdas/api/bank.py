# Copyright (c) Meta Platforms, Inc. and affiliates.

from functools import lru_cache
from datetime import datetime
import json
import signal
import uuid
import bottle
import typing as t
from dataclasses import asdict, dataclass, field
from urllib.parse import quote as uriencode

import boto3
from mypy_boto3_dynamodb.service_resource import Table

from hmalib.common.mappings import HMASignalTypeMapping
from hmalib.common.models.bank import Bank, BankMember, BanksTable, BankMemberSignal
from hmalib.banks import bank_operations as bank_ops
from hmalib.lambdas.api.middleware import (
    jsoninator,
    JSONifiable,
    SubApp,
)
from hmalib.lambdas.api.submit import create_presigned_put_url, create_presigned_url


@dataclass
class AllBanksEnvelope(JSONifiable):
    banks: t.List[Bank]

    def to_json(self) -> t.Dict:
        return {"banks": [bank.to_json() for bank in self.banks]}


@dataclass
class PreviewableBankMember(BankMember):
    """
    A bank-member, but has a preview_url. preview_url should be pre-authorized,
    and of the same content_type as the original media.
    """

    preview_url: str = field(default_factory=lambda: "")


@dataclass
class BankMembersPage(JSONifiable):
    bank_members: t.List[PreviewableBankMember]

    # deserializes to dynamo's exclusive_start_key. Is a dict
    continuation_token: t.Optional[str]

    def to_json(self) -> t.Dict:
        result = asdict(self)
        result.update(bank_members=[member.to_json() for member in self.bank_members])
        return result


@dataclass
class PreviewableBankMemberWithSignals(PreviewableBankMember):
    signals: t.List[BankMemberSignal] = field(default_factory=list)

    def to_json(self) -> t.Dict:
        result = super().to_json()
        result.update(signals=[signal.to_json() for signal in self.signals])
        return result


def with_preview_url(bank_member: BankMember) -> PreviewableBankMember:
    previewable = PreviewableBankMember(**asdict(bank_member))

    if bank_member.storage_bucket is None:
        return previewable

    previewable.preview_url = create_presigned_url(
        bucket_name=bank_member.storage_bucket,
        key=bank_member.storage_key,
        file_type=None,
        expiration=300,
        client_method="get_object",
    )
    return previewable


def with_preview_urls(
    bank_members: t.List[BankMember],
) -> t.List[PreviewableBankMember]:
    """
    For a list of bank_members, converts the storage details into a publicly
    visible image for UI to work with.
    """
    return list(map(with_preview_url, bank_members))


@lru_cache(maxsize=None)
def _get_sqs_client():
    return boto3.client("sqs")


def get_bank_api(
    bank_table: Table,
    bank_user_media_bucket: str,
    submissions_queue_url: str,
    signal_type_mapping: HMASignalTypeMapping,
) -> bottle.Bottle:
    """
    Closure for dependencies of the bank API
    """

    bank_api = SubApp()
    table_manager = BanksTable(
        table=bank_table, signal_type_mapping=signal_type_mapping
    )

    # Bank Management

    @bank_api.get("/get-all-banks", apply=[jsoninator])
    def get_all_banks() -> AllBanksEnvelope:
        """
        Get all banks.
        """
        return AllBanksEnvelope(banks=table_manager.get_all_banks())

    @bank_api.get("/get-bank/<bank_id>", apply=[jsoninator])
    def get_bank(bank_id=None) -> Bank:
        """
        Get a specific bank from a bank_id.
        """
        bank = table_manager.get_bank(bank_id=bank_id)
        return bank

    @bank_api.post("/create-bank", apply=[jsoninator])
    def create_bank() -> Bank:
        """
        Create a bank using only the name, description and an is_active flag,
        and optionally tags.
        """
        return table_manager.create_bank(
            bank_name=bottle.request.json["bank_name"],
            bank_description=bottle.request.json["bank_description"],
            is_active=bottle.request.json["is_active"],
            bank_tags=set(bottle.request.json["bank_tags"]),
        )

    @bank_api.post("/update-bank/<bank_id>", apply=[jsoninator])
    def update_bank(bank_id=None) -> Bank:
        """
        Update name and description for a bank_id.
        """
        return table_manager.update_bank(
            bank_id=bank_id,
            bank_name=bottle.request.json["bank_name"],
            bank_description=bottle.request.json["bank_description"],
            is_active=bottle.request.json["is_active"],
            bank_tags=set(bottle.request.json["bank_tags"]),
        )

    # Member Management

    @bank_api.get("/get-members/<bank_id>", apply=[jsoninator])
    def get_members(bank_id=None) -> BankMembersPage:
        """
        Get a page of bank members. Use the "continuation_token" from this
        response to get subsequent pages.
        """
        continuation_token = (
            bottle.request.query.continuation_token
            and json.loads(bottle.request.query.continuation_token)
            or None
        )

        try:
            content_type = signal_type_mapping.get_content_type_enforce(
                bottle.request.query.content_type
            )
        except:
            bottle.abort(400, "content_type must be provided as a query parameter.")

        db_response = table_manager.get_all_bank_members_page(
            bank_id=bank_id,
            content_type=content_type,
            exclusive_start_key=continuation_token,
        )

        continuation_token = None
        if db_response.last_evaluated_key:
            continuation_token = uriencode(json.dumps(db_response.last_evaluated_key))

        return BankMembersPage(
            bank_members=with_preview_urls(db_response.items),
            continuation_token=continuation_token,
        )

    @bank_api.post("/add-member/<bank_id>", apply=[jsoninator])
    def add_member(bank_id=None) -> PreviewableBankMember:
        """
        Add a bank member. Expects a JSON object with following fields:
        - content_type: ["photo"|"video"]
        - storage_bucket: s3bucket for the media
        - storage_key: key for the media on s3
        - notes: String, any additional notes you want to associate with this
            member.

        Clients would want to use get_media_upload_url() to get a
        storage_bucket, storage_key and a upload_url before using add_member()

        Returns 200 OK with the resulting bank_member. 500 on failure.
        """
        content_type = signal_type_mapping.get_content_type_enforce(
            bottle.request.json["content_type"]
        )
        storage_bucket = bottle.request.json["storage_bucket"]
        storage_key = bottle.request.json["storage_key"]
        notes = bottle.request.json["notes"]
        bank_member_tags = set(bottle.request.json["bank_member_tags"])

        return with_preview_url(
            bank_ops.add_bank_member(
                banks_table=table_manager,
                sqs_client=_get_sqs_client(),
                submissions_queue_url=submissions_queue_url,
                bank_id=bank_id,
                content_type=content_type,
                storage_bucket=storage_bucket,
                storage_key=storage_key,
                raw_content=None,
                notes=notes,
                bank_member_tags=bank_member_tags,
            )
        )

    @bank_api.post("/add-detached-member-signal/<bank_id>", apply=[jsoninator])
    def add_detached_bank_member_signal(bank_id=None) -> BankMemberSignal:
        """
        Add a virtual bank_member (without any associated media) and a
        corresponding signal.

        Requires JSON object with following fields:
        - signal_type: ["pdq"|"pdq_ocr","photo_md5"] -> anything from
          threatexchange.content_type.meta.get_signal_types_by_name()'s keys
        - content_type: ["photo"|"video"] to get the content_type for the
          virtual member.
        - signal_value: the hash to store against this signal. Will
          automatically de-dupe against existing signals.
        """
        content_type = signal_type_mapping.get_content_type_enforce(
            bottle.request.json["content_type"]
        )
        signal_type = signal_type_mapping.get_signal_type_enforce(
            bottle.request.json["signal_type"]
        )
        signal_value = bottle.request.json["signal_value"]

        return bank_ops.add_detached_bank_member_signal(
            banks_table=table_manager,
            bank_id=bank_id,
            content_type=content_type,
            signal_type=signal_type,
            signal_value=signal_value,
        )

    # Miscellaneous
    @bank_api.post("/get-media-upload-url")
    def get_media_upload_url(media_type=None):
        """
        Get a presigned S3 url that can be used by the client to PUT an object.

        Request Payload must be json with the following attributes:

        `media_type` must be something like ['image/gif', 'image/png', 'application/zip']
        `extension` must be a period followed by file extension. eg. `.mp4`, `.jpg`
        """
        extension = bottle.request.json.get("extension")
        media_type = bottle.request.json.get("media_type")

        if (not extension) or extension[0] != ".":
            bottle.abort(400, "extension must start with a period. eg. '.mp4'")

        id = str(uuid.uuid4())
        today_fragment = datetime.now().isoformat("|").split("|")[0]  # eg. 2019-09-12
        s3_key = f"bank-media/{media_type}/{today_fragment}/{id}{extension}"

        return {
            "storage_bucket": bank_user_media_bucket,
            "storage_key": s3_key,
            "upload_url": create_presigned_put_url(
                bucket_name=bank_user_media_bucket,
                key=s3_key,
                file_type=media_type,
                expiration=3600,
            ),
        }

    @bank_api.get("/get-member/<bank_member_id>", apply=[jsoninator])
    def get_member(bank_member_id=None) -> PreviewableBankMemberWithSignals:
        """
        Get a bank member with signals...
        """
        member = table_manager.get_bank_member(bank_member_id=bank_member_id)
        signals = table_manager.get_signals_for_bank_member(
            bank_member_id=bank_member_id
        )

        return PreviewableBankMemberWithSignals(
            **asdict(with_preview_url(member)), signals=signals
        )

    @bank_api.post("/update-bank-member/<bank_member_id>", apply=[jsoninator])
    def update_bank_member(bank_member_id=None) -> BankMember:
        """
        Update notes and tags for a bank_member_id.
        """
        return table_manager.update_bank_member(
            bank_member_id=bank_member_id,
            notes=bottle.request.json["notes"],
            bank_member_tags=set(bottle.request.json["bank_member_tags"]),
        )

    @bank_api.post("/remove-bank-member/<bank_member_id>")
    def remove_bank_member(bank_member_id: str):
        """
        Remove bank member signals from the processing index and mark
        bank_member as is_removed=True.

        Returns empty json object.
        """
        bank_ops.remove_bank_member(
            banks_table=table_manager,
            bank_member_id=bank_member_id,
        )
        return {}

    return bank_api
