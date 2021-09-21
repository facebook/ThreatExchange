from decimal import Decimal
from hmalib.models import PipelineHashRecord, HashRecordQuery
import boto3
import uuid
from datetime import datetime
from threatexchange.signal_type.pdq import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal
from boto3.dynamodb.conditions import Key

table = boto3.resource("dynamodb").Table("dipanjanm-HMADataStore")
u = uuid.uuid4()

p = PipelineHashRecord(
    content_id=str(u),
    signal_type=VideoMD5Signal,
    content_hash="39bf3dc7f9659aefeac07b598057b86c",
    updated_at=datetime.now(),
    # signal_specific_attributes={"MD5_Version": "lol-md5-no-versions"},
    signal_specific_attributes={},
)
p.write_to_table(table)

q = PipelineHashRecord.get_from_content_id(table, str(u))
print(q)

# key_condition_exp = Key("PK").eq(f"c#{str(u)}") & Key("SK").begins_with("type#")

# r = table.query(
#     KeyConditionExpression=key_condition_exp,
#     ProjectionExpression=HashRecordQuery.DEFAULT_PROJ_EXP,
# )
# print(r)
