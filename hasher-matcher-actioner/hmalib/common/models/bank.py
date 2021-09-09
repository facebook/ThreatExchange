# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import typing as t
from datetime import datetime
from dataclasses import asdict, dataclass
import uuid
from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb.service_resource import Table

from threatexchange.content_type.content_base import ContentType
from threatexchange.signal_type.signal_base import SignalType

from hmalib.common.models.models_base import DynamoDBItem

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
BankMember            | <bank_id>                 | member#<bank_member_id>        
BankMemberSignal      | <bank_id>                 | signal#<signal_id>             
<signal_id>           | signal_type#<signal_type> | signal_value#<signal_value>    
|
Bank objects are all stored under the same partition key because all bank
information is expected to be less than 10GB. Also, when a bank is deleted, it
is removed from the (2) BankNameIndex. To be able to find it, there must be
another way. That is provided by the "known" PK of #bank_object

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
    """

    bank_id: str
    bank_member_id: str

    content_type: t.Type[ContentType]

    # Will contain either the media_url (in case of photos / videos / pdfs) or
    # the raw_content in case of plain text.
    media_url: str
    raw_content: str

    notes: str

    created_at: datetime
    updated_at: datetime


@dataclass
class BankMemberSignal(DynamoDBItem):
    """
    Describes a signal extracted from a bank member.
    """

    bank_id: str
    signal_id: str

    signal_type: t.Type[ContentType]
    signal_value: str

    updated_at: datetime


@dataclass
class BankedSignalEntry(DynamoDBItem):
    """
    Enforces uniqueness for a signal_type and signal_vlaue.
    """

    signal_type: t.Type[SignalType]
    signal_value: str

    signal_id: str


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

    def add_bank_member(
        self,
        bank_id: str,
        content_type: t.Type[ContentType],
        media_url: t.Optional[str],
        raw_content: t.Optional[str],
        notes: str,
    ) -> BankMember:
        pass
