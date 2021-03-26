# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import logging

def get_logger(name=__name__, level=logging.INFO):
    """
    This pattern prevents creates implicitly creating a root logger by creating the sub-logger named __name__
    Also by default sets level to INFO
    """

    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger

@dataclass
class ThreatExchangeS3Adapter():

    THREAT_EXCHANGE_DATA_BUCKET_NAME = os.environ["THREAT_EXCHANGE_DATA_BUCKET_NAME"]
    THREAT_EXCHANGE_DATA_FOLDER = os.environ["THREAT_EXCHANGE_DATA_FOLDER"]

    """
    Adapter for reading data stored in ThreatExchange of a specific data type

    Should probably refactor and merge with ThreatUpdateS3Store
    """

    self.metrics_logger : metircs.lamda_with_datafiles

    def get_data(self):
        """
        gets all (.pdq.te) files in TE
        """
        logger.info("Retreiving PDQ Data from S3")
        with metrics.timer(self.metrics_logger.download_datafiles):
            s3_bucket_files = s3_client.list_objects_v2(
                Bucket=THREAT_EXCHANGE_DATA_BUCKET_NAME,
                Prefix=THREAT_EXCHANGE_DATA_FOLDER,
            )["Contents"]
            logger.info("Found %d Files", len(s3_bucket_files))

            typed_data_files = [
                _get_file(file["Key"])
                for file in s3_bucket_files
                if file["Key"].endswith(self.data_type_key_suffix)
            ]
            logger.info("Found %d PDQ Files", len(typed_data_files))

        with metrics.timer(self.metrics_logger.parse_datafiles):
            logger.info("Parsing PDQ Hash files")
            typed_data = [_parse_file(**typed_data_file) for typed_data_file in typed_data_files]

        return typed_data

    @property
    def data_type_key_suffix(self):
        raise NotImplementedError()

    @property
    def data_file_columns(self):
        raise NotImplementedError()

    def _get_file(self, file_name: str) -> t.Dict[str, t.Any]:
        return {
            "file_name": file_name,
            "data_file": s3_client.get_object(
                Bucket=THREAT_EXCHANGE_DATA_BUCKET_NAME, Key=file_name
            ),
        }

    def _parse_file(
        self
        file_name: str,
        data_file: S3FileT
    ) -> t.List[HashRowT]:
        data_reader = csv.DictReader(
            codecs.getreader("utf-8")(pdq_data_file["Body"]),
            fieldnames=self.data_file_columns,
        )
        return [
            (
                row["hash"],
                # Also add hash to metadata for easy look up on match
                {
                    "id": int(row["id"]),
                    "hash": row["hash"],
                    "source": "te",  # default for now to make downstream easier to generalize
                    "privacy_groups": [file_name.split("/")[-1].split(".")[0]],
                },
            )
            for row in data_reader
        ]

class ThreatExchangeS3PDQAdapter(ThreatExchangeS3Adapter):
    THREAT_EXCHANGE_PDQ_KEY_SUFFIX = os.environ["THREAT_EXCHANGE_PDQ_KEY_SUFFIX"]

    @property
    def data_type_key_suffix(self):
        return THREAT_EXCHANGE_PDQ_KEY_SUFFIX

    @property
    def data_file_columns(self):
        return ["hash", "id", "timestamp", "tags"]




IMPLEMENTED_DATA_TYPES = ["HASH_PDQ"]
