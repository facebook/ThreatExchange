# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import typing as t
from datetime import datetime
from dataclasses import asdict, dataclass, field
from enum import Enum
import uuid

from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import Table

from threatexchange.content_type.content_base import ContentType
from threatexchange.content_type.meta import (
    get_content_type_for_name,
    get_signal_types_by_name,
)
from threatexchange.signal_type.signal_base import SignalType

from hmalib.common.models.models_base import (
    DynamoDBCursorKey,
    DynamoDBItem,
    PaginatedResponse,
)

"""
# DynamoDB Table HMABanks

## Models
Stores banks and bank-members & bank-member signals.

BankMemberSignals are signals extracted from the content in the bank member
object. However, <signal_id> is unique for a signal_type, signal_value tuple.
This is enforced by the 4th type of entry in the default table index.

## Indices

1. Default Table Index
Item                  | PK                        | SK                             
----------------------|---------------------------|------------------------------
Bank                  | #bank_object              | <bank_id>                      
BankMember            | <bank_id>#<content_type>  | member#<bank_member_id>        
BankMemberSignal      | <bank_member_id>          | signal#<signal_id>             
<signal_id>           | signal_type#<signal_type> | signal_value#<signal_value>    

Bank objects are all stored under the same, static partition key because all
bank information is expected to be less than 10GB. Also, when a bank is deleted,
it is removed from the (2) BankNameIndex. To be able to find it, there must be
another way. That is provided by the "known" PK of #bank_object

BankMembers have a PK of <bank_id>#<content_type>. This allows easy querying for
pages of members for a specific content_type. At this point, I do not see need
for querying a bank_member without knowing its content_type. Should that need
arise (and it might soon), we can use override MemberToSignalIndex below with a
static SK: MemberToSignalIndex eg. PK=<bank_member_id>, SK=#member_object

2. BankNameIndex
   A sparse index. Only contains BankObjects. Used to check if bank_name is
   repeated. Because it is a sparse index, scans are cheap too. Project all
   attributes. Cheap and useful if looking up by name.
PK             SK               Item
<bank_name>    <bank_id>        ALL(BankObject)

3. MemberToSignalIndex
   Use for getting signals for a member. Sparse Index.
PK                SK                        Item
<bank_member_id>  <bank_member_signal_id>   KEYS_ONLY(BankMemberSignal)

4. SignalIndex
   Use to get a signal by its ID. Note, there can be multiple entries if the
   same signal is emitted by multiple banks.
PK                        SK            Item
<bank_member_signal_id>   <bank_id>     KEYS_ONLY(BankMemberSignal)

5. PendingBankMemberSignalsIndex
   A sparse index. Only contains BankMemberSignalObjects that haven't yet been
   processed into the index. Additions and Removals can both be processed. The
   indexer must scan this index, for each entry, get the BankMember and
   BankMemberSignal. As the indexer processes them in, it will remove them from
   this sparse GSI.
PK              SK              Item
<signal_type>   <updated_at>    KEYS_ONLY(BankMemberSignal)
"""


@dataclass
class Bank(DynamoDBItem):
    """
    Describes a bank object. A bank is an aggregate of bank-members.
    """

    BANK_OBJECT_PARTITION_KEY = "#bank_object"

    bank_id: str  # generated using uuid

    bank_name: str
    bank_description: str

    created_at: datetime

    # Gets changed on updates to the bank object, not its members.
    updated_at: datetime

    def to_dynamodb_item(self) -> t.Dict:
        return {
            # Main Index
            "PK": self.BANK_OBJECT_PARTITION_KEY,
            "SK": self.bank_id,
            # GSI: BankNameIndex
            "BankNameIndex-BankName": self.bank_name,
            "BankNameIndex-BankId": self.bank_id,
            # Attributes
            "BankId": self.bank_id,
            "BankName": self.bank_name,
            "BankDescription": self.bank_description,
            "CreatedAt": self.created_at.isoformat(),
            "UpdatedAt": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dynamodb_item(cls, item: t.Dict) -> "Bank":
        return cls(
            bank_id=item["BankId"],
            bank_name=item["BankName"],
            bank_description=item["BankDescription"],
            created_at=datetime.fromisoformat(item["CreatedAt"]),
            updated_at=datetime.fromisoformat(item["UpdatedAt"]),
        )

    def to_json(self) -> t.Dict:
        """Used in APIs."""
        result = asdict(self)
        result.update(
            created_at=self.created_at.isoformat(),
            updated_at=self.updated_at.isoformat(),
        )
        return result


@dataclass
class BankMember(DynamoDBItem):
    """
    Describes a bank member. A bank member is a piece of content. eg. text,
    video, photo that a partner wants to match against.

    A BankMember can also be virtual. Which means the actual media is
    unavailable. This could happen if the bank is sycned with a source that only
    provides hashes, or it could be that the media has been removed to comply
    with retention policies. Since virtual could be a loaded term, we use the
    more explicit and accurate `is_media_unavailable attribute`.
    """

    BANK_MEMBER_ID_PREFIX = "member#"

    BANK_MEMBER_ID_INDEX = "BankMemberIdIndex"
    BANK_MEMBER_ID_INDEX_BANK_MEMBER_ID = f"{BANK_MEMBER_ID_INDEX}-BankMemberId"

    bank_id: str
    bank_member_id: str

    content_type: t.Type[ContentType]

    # When storing media files, store the bucket and the key. If files are
    # deleted because of legal / retention policies, this indicator will stay
    # as-is even if the actual s3 object is deleted.
    storage_bucket: t.Optional[str]
    storage_key: t.Optional[str]

    # In case we are storing the content directly in dynamodb.
    raw_content: t.Optional[str]

    notes: str

    created_at: datetime
    updated_at: datetime

    is_removed: bool = field(default=False)
    is_media_unavailable: bool = field(default=False)

    @classmethod
    def get_pk(cls, bank_id: str, content_type: t.Type[ContentType]):
        return f"{bank_id}#{content_type.get_name()}"

    @classmethod
    def get_sk(cls, bank_member_id: str):
        return f"{cls.BANK_MEMBER_ID_PREFIX}{bank_member_id}"

    def to_dynamodb_item(self) -> t.Dict:
        return {
            # Main Index
            "PK": self.get_pk(self.bank_id, self.content_type),
            "SK": self.get_sk(self.bank_member_id),
            # BankMemberId Index
            self.BANK_MEMBER_ID_INDEX_BANK_MEMBER_ID: self.bank_member_id,
            # Attributes
            "BankId": self.bank_id,
            "BankMemberId": self.bank_member_id,
            "ContentType": self.content_type.get_name(),
            "StorageBucket": self.storage_bucket,
            "StorageKey": self.storage_key,
            "RawContent": self.raw_content,
            "Notes": self.notes,
            "CreatedAt": self.created_at.isoformat(),
            "UpdatedAt": self.updated_at.isoformat(),
            "IsRemoved": self.is_removed,
            "IsMediaUnavailable": self.is_media_unavailable,
        }

    @classmethod
    def from_dynamodb_item(cls, item: t.Dict) -> "BankMember":
        return cls(
            bank_id=item["BankId"],
            bank_member_id=item["BankMemberId"],
            content_type=get_content_type_for_name(item["ContentType"]),
            storage_bucket=item["StorageBucket"],
            storage_key=item["StorageKey"],
            raw_content=item["RawContent"],
            notes=item["Notes"],
            created_at=datetime.fromisoformat(item["CreatedAt"]),
            updated_at=datetime.fromisoformat(item["UpdatedAt"]),
            is_removed=item["IsRemoved"],
            is_media_unavailable=item["IsMediaUnavailable"],
        )

    def to_json(self) -> t.Dict:
        """Used in APIs."""
        result = asdict(self)
        result.update(
            content_type=self.content_type.get_name(),
            created_at=self.created_at.isoformat(),
            updated_at=self.updated_at.isoformat(),
        )
        return result


class BankMemberSignalStatus(Enum):
    """
    Bank member signals are processed into the respective signal_type indexes.
    This enum governs the possible states the BankMemberSignal object can be
    in. This influences whether or not a BankMemberSignal object is present in
    the PendingBankMemberSignalsIndex.
    """

    # Implies that this needs to be processed now.
    PENDING = "PENDING"

    # Has been processed into an index.
    PROCESSED = "PROCESSED"

    # State machine purists will note that we do not have a PROCESSING stage
    # which will take a lock and prevent double processing for records. However,
    # in our case, there is no cost to double processing as long as records are
    # processed in order. i.e chronologically.


@dataclass
class BankMemberSignal(DynamoDBItem):
    """
    Describes a signal extracted from a bank member.
    """

    bank_id: str
    bank_member_id: str

    signal_id: str
    signal_type: t.Type[SignalType]
    signal_value: str

    status: BankMemberSignalStatus

    updated_at: datetime

    PENDING_BANK_MEMBER_SIGNALS_INDEX = "PendingBankMemberSignalIndex"
    PENDING_BANK_MEMBER_SIGNALS_INDEX_SIGNAL_TYPE = (
        f"{PENDING_BANK_MEMBER_SIGNALS_INDEX}-SignalType"
    )
    PENDING_BANK_MEMBER_SIGNALS_INDEX_UPDATED_AT = (
        f"{PENDING_BANK_MEMBER_SIGNALS_INDEX}-UpdatedAt"
    )

    @classmethod
    def get_pk(cls, bank_member_id):
        return bank_member_id

    @classmethod
    def get_sk(cls, signal_id):
        return f"signal#{signal_id}"

    def to_dynamodb_item(self) -> t.Dict:
        item = {
            # Main Index
            "PK": self.get_pk(bank_member_id=self.bank_member_id),
            "SK": self.get_sk(signal_id=self.signal_id),
            # Attributes
            "BankId": self.bank_id,
            "BankMemberId": self.bank_member_id,
            "SignalId": self.signal_id,
            "SignalType": self.signal_type.get_name(),
            "SignalValue": self.signal_value,
            "UpdatedAt": self.updated_at.isoformat(),
            "Status": self.status.name,
        }

        if self.status == BankMemberSignalStatus.PENDING:
            item.update(
                **{
                    self.PENDING_BANK_MEMBER_SIGNALS_INDEX_SIGNAL_TYPE: self.signal_type.get_name(),
                    self.PENDING_BANK_MEMBER_SIGNALS_INDEX_UPDATED_AT: self.updated_at.isoformat(),
                }
            )

        return item

    @classmethod
    def from_dynamodb_item(cls, item: t.Dict) -> "BankMemberSignal":
        return cls(
            bank_id=item["BankId"],
            bank_member_id=item["BankMemberId"],
            signal_id=item["SignalId"],
            signal_type=get_signal_types_by_name()[item["SignalType"]],
            signal_value=item["SignalValue"],
            updated_at=datetime.fromisoformat(item["UpdatedAt"]),
            status=BankMemberSignalStatus(item["Status"]),
        )

    def to_json(self) -> t.Dict:
        """Used in APIs."""
        result = asdict(self)
        result.update(
            signal_type=self.signal_type.get_name(),
            updated_at=self.updated_at.isoformat(),
            status=self.status.value,
        )
        return result

    @classmethod
    def unmark(cls, table: Table, bank_member_id: str, signal_id: str):
        """
        Updates the status to processed, the updated_at value to now() and
        removes from the PendingBankMemberSignalIndex.

        To do this in a single ddb call, we use an update_item statement which
        REMOVES the GSI values, thus removing them from the index.
        """
        table.update_item(
            Key={
                "PK": cls.get_pk(bank_member_id=bank_member_id),
                "SK": cls.get_sk(signal_id=signal_id),
            },
            UpdateExpression=f"SET Status = :status, UpdatedAt = :updated_at  REMOVE {cls.PENDING_BANK_MEMBER_SIGNALS_INDEX_SIGNAL_TYPE}, {cls.PENDING_BANK_MEMBER_SIGNALS_INDEX_UPDATED_AT}",
            ExpressionAttributeValues={
                ":status": BankMemberSignalStatus.PROCESSED.value,
                ":updated_at": datetime.now().isoformat(),
            },
        )


@dataclass
class BankedSignalEntry(DynamoDBItem):
    """
    Enforces uniqueness for a signal_type and signal_vlaue.
    """

    signal_type: t.Type[SignalType]
    signal_value: str

    signal_id: str

    @classmethod
    def get_pk(cls, signal_type: t.Type[SignalType]) -> str:
        return f"signal_type#{signal_type.get_name()}"

    @classmethod
    def get_sk(self, signal_value: str) -> str:
        return f"signal_value#{signal_value}"

    def to_dynamodb_item(self) -> t.Dict:
        # Raise an error so that write_to_table() fails. We never want to do that.
        raise Exception("Do not write BankedSignalEntry to DDB directly!")

    @classmethod
    def get_unique(
        cls, table: Table, signal_type: t.Type[SignalType], signal_value: str
    ) -> "BankedSignalEntry":
        """
        Write to the table if PK / SK does not exist. In either case (exists,
        not exists), return the current unique entry.

        This is a special use-case for BankedSignalEntry. If this is useful to
        other models, we can move it to a mixin or to dynamodb item. If trying
        to generify, note how the update_item query needs a custom update query
        based on what you are trying to write. Generifying may be harder than it
        seems.
        """
        result = table.update_item(
            Key={
                "PK": cls.get_pk(signal_type),
                "SK": cls.get_sk(signal_value),
            },
            UpdateExpression="SET SignalId = if_not_exists(SignalId, :signal_id), SignalType = :signal_type, SignalValue = :signal_value",
            ExpressionAttributeValues={
                # Note we are generating a new uuid even though we don't always
                # expect it to get written. AFAIK, uuids are inexhaustible, and
                # generation performance is good enough to not worry about it.
                ":signal_id": str(uuid.uuid4()),
                ":signal_type": signal_type.get_name(),
                ":signal_value": signal_value,
            },
            ReturnValues="ALL_NEW",
        ).get("Attributes")

        assert result is not None

        return BankedSignalEntry(
            signal_type=get_signal_types_by_name()[result["SignalType"]],
            signal_value=t.cast(str, result["SignalValue"]),
            signal_id=t.cast(str, result["SignalId"]),
        )


class BanksTable:
    """
    Provides query + update methods on the entire table.

    This is a departure from the norm in models from the content, pipeline and
    signals modules. There, we provide query methods in the model itself. But,
    here we're trying a single 'manager' for all classes of items in the table.
    """

    def __init__(self, table: Table):
        self._table = table

    def create_bank(self, bank_name: str, bank_description: str) -> Bank:
        new_bank_id = str(uuid.uuid4())
        now = datetime.now()
        bank = Bank(
            bank_id=new_bank_id,
            bank_name=bank_name,
            bank_description=bank_description,
            created_at=now,
            updated_at=now,
        )
        bank.write_to_table(table=self._table)
        return bank

    def get_bank(self, bank_id: str) -> Bank:
        return Bank.from_dynamodb_item(
            self._table.get_item(
                Key={"SK": bank_id, "PK": Bank.BANK_OBJECT_PARTITION_KEY}
            )["Item"]
        )

    def get_all_banks(self) -> t.List[Bank]:
        return [
            Bank.from_dynamodb_item(item)
            for item in self._table.scan(IndexName="BankNameIndex")["Items"]
        ]

    def update_bank(
        self,
        bank_id: str,
        bank_name: t.Optional[str],
        bank_description: t.Optional[str],
    ) -> Bank:
        bank = Bank.from_dynamodb_item(
            self._table.get_item(
                Key={"SK": bank_id, "PK": Bank.BANK_OBJECT_PARTITION_KEY}
            )["Item"]
        )

        if bank_name:
            bank.bank_name = bank_name

        if bank_description:
            bank.bank_description = bank_description

        if bank_name or bank_description:
            bank.updated_at = datetime.now()
            bank.write_to_table(table=self._table)

        return bank

    def get_all_bank_members_page(
        self,
        bank_id: str,
        content_type=t.Type[ContentType],
        exclusive_start_key: t.Optional[DynamoDBCursorKey] = None,
    ) -> PaginatedResponse[BankMember]:
        # NOTE: This does not yet filter out is_removed bank_members
        PAGE_SIZE = 100
        expected_pk = BankMember.get_pk(bank_id=bank_id, content_type=content_type)

        if not exclusive_start_key:
            result = self._table.query(
                ScanIndexForward=False,
                KeyConditionExpression=Key("PK").eq(expected_pk),
                Limit=PAGE_SIZE,
            )
        else:
            result = self._table.query(
                ScanIndexForward=False,
                KeyConditionExpression=Key("PK").eq(expected_pk),
                ExclusiveStartKey=exclusive_start_key,
                Limit=PAGE_SIZE,
            )

        return PaginatedResponse(
            t.cast(DynamoDBCursorKey, result.get("LastEvaluatedKey", None)),
            [BankMember.from_dynamodb_item(item) for item in result["Items"]],
        )

    def add_bank_member(
        self,
        bank_id: str,
        content_type: t.Type[ContentType],
        storage_bucket: t.Optional[str],
        storage_key: t.Optional[str],
        raw_content: t.Optional[str],
        notes: str,
        is_media_unavailable: bool = False,
    ) -> BankMember:
        """
        Adds a member to the bank. DOES NOT enforce retroaction. DOES NOT
        extract signals. Merely a facade to the storage layer. Additional
        co-ordination (hashing, retroactioning, index updates) should happen via
        hmalib.banks.bank_operations module.
        """
        new_member_id = str(uuid.uuid4())
        now = datetime.now()
        bank_member = BankMember(
            bank_id=bank_id,
            bank_member_id=new_member_id,
            content_type=content_type,
            storage_bucket=storage_bucket,
            storage_key=storage_key,
            raw_content=raw_content,
            notes=notes,
            created_at=now,
            updated_at=now,
            is_media_unavailable=is_media_unavailable,
        )

        bank_member.write_to_table(self._table)
        return bank_member

    def remove_bank_member(self, bank_id: str, bank_member_id: str):
        """
        Removes the bank member and associated signals from the bank. Merely
        marks as removed, does not physically delete from the store. DOES NOT
        stop matching until index is updated. DOES NOT undo any actions already
        taken.
        """
        bank_member = BankMember.from_dynamodb_item(
            self._table.get_item(
                Key={"PK": bank_id, "SK": BankMember.get_sk(bank_member_id)}
            )["Item"]
        )
        bank_member.is_removed = False
        bank_member.write_to_table(self._table)

    def add_bank_member_signal(
        self,
        bank_id: str,
        bank_member_id: str,
        signal_type: t.Type[SignalType],
        signal_value: str,
    ) -> BankMemberSignal:
        """
        Adds a BankMemberSignal entry. First, identifies if a signal for the
        corresponding (type, value) tuple exists, if so, reuses it, it not,
        creates a new one.

        Returns a BankMemberSignal object. Clients **should not** care whether
        this is a new signal_id or not.

        This check is being done here because signal uniqueness is enforced by
        the same table. If this were being done in a different table/store, we
        could be doing the check at a different layer eg.
        hmalib.banks.bank_operations.
        """
        # First, we get a unique signal_id!
        signal_id = BankedSignalEntry.get_unique(
            self._table, signal_type=signal_type, signal_value=signal_value
        ).signal_id

        # Next, we create the bank member signal
        member_signal = BankMemberSignal(
            bank_id=bank_id,
            bank_member_id=bank_member_id,
            signal_id=signal_id,
            signal_type=signal_type,
            signal_value=signal_value,
            updated_at=datetime.now(),
            status=BankMemberSignalStatus.PENDING,
        )
        member_signal.write_to_table(self._table)
        return member_signal

    def add_detached_bank_member_signal(
        self,
        bank_id: str,
        content_type: t.Type[ContentType],
        signal_type: t.Type[SignalType],
        signal_value: str,
    ) -> BankMemberSignal:
        """
        Adds a BankMemberSignal without a needing a related BankMember. Pretty
        much the same as add_bank_member_signal otherwise.

        Creates a BankMember with a is_media_unavailable=True.
        """
        bank_member = self.add_bank_member(
            bank_id=bank_id,
            content_type=content_type,
            storage_bucket=None,
            storage_key=None,
            raw_content=None,
            notes="",
            is_media_unavailable=True,
        )

        return self.add_bank_member_signal(
            bank_id=bank_id,
            bank_member_id=bank_member.bank_member_id,
            signal_type=signal_type,
            signal_value=signal_value,
        )

    def unmark_bank_member_signal(self, bank_member_id: str, signal_id: str):
        """
        Remove the bank-member-signal from the pending index.
        """
        BankMemberSignal.unmark(
            self._table, bank_member_id=bank_member_id, signal_id=signal_id
        )

    def get_bank_member_signals_to_process(
        self, signal_type: t.Type[SignalType], limit: int = 100
    ):
        return [
            BankMemberSignal.from_dynamodb_item(item)
            for item in self._table.query(
                IndexName=BankMemberSignal.PENDING_BANK_MEMBER_SIGNALS_INDEX,
                KeyConditionExpression=Key("PK").eq(signal_type.get_name()),
                Limit=limit,
            )["Items"]
        ]

    def get_signals_for_bank_member(
        self, bank_member_id: str
    ) -> t.List[BankMemberSignal]:
        return [
            BankMemberSignal.from_dynamodb_item(item)
            for item in self._table.query(
                KeyConditionExpression=Key("PK").eq(
                    BankMemberSignal.get_pk(bank_member_id=bank_member_id)
                )
            )["Items"]
        ]

    def get_bank_member(self, bank_member_id: str) -> BankMember:
        member_keys = self._table.query(
            IndexName=BankMember.BANK_MEMBER_ID_INDEX,
            KeyConditionExpression=Key(
                BankMember.BANK_MEMBER_ID_INDEX_BANK_MEMBER_ID
            ).eq(bank_member_id),
        )["Items"][0]

        return BankMember.from_dynamodb_item(
            self._table.get_item(
                Key={"PK": member_keys["PK"], "SK": member_keys["SK"]}
            )["Item"]
        )
