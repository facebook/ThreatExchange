from mypy_boto3_dynamodb.service_resource import Table

class _IDynamoDBItem():
    """
    Clowny type as an interfaces. True interfaces in python are nightmares.
    """
    def to_dynamodb_item(self) -> dict:
        pass

class HashStore:
    """
    Stores all kinds of hashes into a dynamodb.
    """

    def __init__(self, table: Table):
        self._table = table

    def add_hash(self, record: _IDynamoDBItem):
        self._table.put_item(Item=record.to_dynamodb_item())
