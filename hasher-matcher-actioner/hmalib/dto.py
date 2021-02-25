import datetime
import typing as t

"""
Not enforceable because named tuples can't have multiple inheritance, but all
DTO classes in this module should implement methods `to_dynamodb_item(self)` and
`to_sqs_message(self)`
"""

class PDQHashRecord(t.NamedTuple):
    """
    Successful execution at the hasher produces this record.
    """

    content_key: str
    content_hash: str
    quality: int
    timestamp: datetime.datetime  # ISO-8601 formatted

    @staticmethod
    def get_dynamodb_pk(key: str):
        return f"c#{key}"

    def to_dynamodb_item(self) -> dict:
        return {
            "PK": PDQHashRecord.get_dynamodb_pk(self.content_key),
            "SK": "type:pdq",
            "ContentHash": self.content_hash,
            "Quality": self.quality,
            "Timestamp": self.timestamp.isoformat(),
            "HashType": "pdq",
        }

    def to_sqs_message(self) -> dict:
        return {
            "hash": self.content_hash,
            "type": "pdq",
            "key": self.content_key
        }
