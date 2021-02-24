from boto3.resources.factory import dynamodb


class HashStore:
    """ Stores all kinds of hashes into a dynamodb. """

    def __init__(self, table: dynamodb.Table):
        self._table = table

    def add_hash(self, record: HashRecord):
        self._table.put_item(Item=record.to_dynamodb_item())
