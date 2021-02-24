import datetime
import typing as t

# Not enforceable because named tuples can't have multiple inheritance, but all
# DTO classes in this module should implement methods
# `to_dynamodb_item(self)`
# and `to_sqs_message(self)`


class PDQHashRecord(t.NamedTuple):
    """Successful execution at the hasher produces this record.

    At present, we only use these records to write to dynamodb, so this is in
    the storage module, but we can move this out.
    """

    content_key: str
    content_hash: str
    quality: int
    timestamp: datetime.datetime  # ISO-8601 formatted

    def to_dynamodb_item(self) -> dict:
        return {
            "PK": "c#{}".format(self.content_key),
            "SK": "type:pdq",
            "ContentHash": self.content_hash,
            "Quality": quality,
            "Timestamp": timestamp.isoformat(),
            "HashType": "pdq",
        }

    def to_sqs_message(self) -> dict:
        return {"hash": pdq_hash, "type": "pdq", "key": key}
