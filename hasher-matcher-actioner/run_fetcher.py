import os

os.environ[
    "THREAT_EXCHANGE_DATA_BUCKET_NAME"
] = "dipanjanm-hashing-data20210402200425191500000003"
os.environ["THREAT_EXCHANGE_DATA_FOLDER"] = "threat_exchange_data/"
os.environ["CONFIG_TABLE_NAME"] = "dipanjanm-HMAConfig"
os.environ["DYNAMODB_DATASTORE_TABLE"] = "dipanjanm-HMADataStore"
os.environ[
    "THREAT_EXCHANGE_API_TOKEN_SECRET_NAME"
] = "threatexchange/dipanjanm_api_tokens"

from hmalib.lambdas.fetcher import lambda_handler

lambda_handler(None, None)
