# Copyright (c) Meta Platforms, Inc. and affiliates.

import collections
import csv
import functools
import warnings
import io
import json
import boto3
import csv
import codecs
from pathlib import Path
from datetime import datetime

from dataclasses import dataclass, field
import typing as t

from botocore.errorfactory import ClientError
from mypy_boto3_s3 import Client as S3Client
from mypy_boto3_s3.service_resource import Bucket
from threatexchange.exchanges.clients.fb_threatexchange import threat_updates as tu
from threatexchange.cli.dataset.simple_serialization import HMASerialization
from threatexchange.exchanges.clients.fb_threatexchange.descriptor import (
    SimpleDescriptorRollup,
    ThreatDescriptor,
)
from threatexchange.signal_type.signal_base import SignalType
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.pdq import PdqSignal
from hmalib.common.mappings import HMASignalTypeMapping


from hmalib.common.models.signal import (
    ThreatExchangeSignalMetadata,
    PendingThreatExchangeOpinionChange,
)
from hmalib import metrics
from hmalib.common.logging import get_logger
from hmalib.indexers.metadata import (
    BaseIndexMetadata,
    ThreatExchangeIndicatorIndexMetadata,
    THREAT_EXCHANGE_SOURCE_SHORT_CODE,
)

logger = get_logger(__name__)


@functools.lru_cache(maxsize=None)
def get_dynamodb():
    return boto3.resource("dynamodb")


@functools.lru_cache(maxsize=None)
def get_s3_client():
    return boto3.client("s3")


# A hash row is a tuple of the hash_value and a sequence of metadata object.
# Remember, a single hash may have multiple metadata objects. One from
# threatexchange, one from banks, another one from threatexchange, but a
# different privacy group.
#
# Use mutable sequence instead of list here because we need subclasses of
# BaseIndexMetadata and t.List is not co-variant in mypy's grammar.
HashRowT = t.Tuple[str, t.MutableSequence[BaseIndexMetadata]]

# Signal types that s3_adapters should support
KNOWN_SIGNAL_TYPES: t.List[t.Type[SignalType]] = [VideoMD5Signal, PdqSignal]


@dataclass
class S3ThreatDataConfig:

    SOURCE_STR = THREAT_EXCHANGE_SOURCE_SHORT_CODE

    threat_exchange_data_bucket_name: str
    threat_exchange_data_folder: str


@dataclass
class ThreatExchangeS3Adapter:
    """
    Adapter for reading ThreatExchange data stored in S3. Concrete implementations
    are for a specific indicator type such as PDQ

    Assumes CSV file format

    Should probably refactor and merge with ThreatUpdateS3Store for writes
    """

    metrics_logger: metrics.lambda_with_datafiles
    S3FileT = t.Dict[str, t.Any]
    config: S3ThreatDataConfig
    last_modified: t.Dict[str, str] = field(default_factory=dict)

    def load_data(self) -> t.Dict[str, t.List[HashRowT]]:
        """
        loads all data from all files in TE that are of the concrete implementations indicator type

        returns a mapping from file name to list of rows
        """
        logger.info("Retreiving %s Data from S3", self.file_type_str_name)
        with metrics.timer(self.metrics_logger.download_datafiles):
            # S3 doesnt have a built in concept of folders but the AWS UI
            # implements folder-like functionality using prefixes. We follow
            # this same convension here using folder name in a prefix search
            s3_bucket_files = get_s3_client().list_objects_v2(
                Bucket=self.config.threat_exchange_data_bucket_name,
                Prefix=self.config.threat_exchange_data_folder,
            )["Contents"]
            logger.info("Found %d Files", len(s3_bucket_files))

            typed_data_files = {
                file["Key"]: self._get_file(file["Key"])
                for file in s3_bucket_files
                if file["Key"].endswith(self.indicator_type_file_extension)
            }
            logger.info(
                "Found %d %s Files", len(typed_data_files), self.file_type_str_name
            )

        with metrics.timer(self.metrics_logger.parse_datafiles):
            logger.info("Parsing %s Hash files", self.file_type_str_name)
            typed_data = {
                file_name: self._parse_file(**typed_data_file)
                for file_name, typed_data_file in typed_data_files.items()
            }
        return typed_data

    @property
    def indicator_type_file_extension(self):
        """
        What is the extension for files of this indicator type

        eg. hash_pdq.te indicates PDQ files
        """
        raise NotImplementedError()

    @property
    def file_type_str_name(self):
        """
        What types of files does the concrete implementation correspond to

        for logging only
        """
        raise NotImplementedError()

    @property
    def indicator_type_file_columns(self):
        """
        What are the csv columns when this type of data is stored in S3
        """
        raise NotImplementedError()

    def _get_file(self, file_name: str) -> t.Dict[str, t.Any]:
        return {
            "file_name": file_name,
            "data_file": get_s3_client().get_object(
                Bucket=self.config.threat_exchange_data_bucket_name, Key=file_name
            ),
        }

    def _parse_file(self, file_name: str, data_file: S3FileT) -> t.List[HashRowT]:
        data_reader = csv.DictReader(
            codecs.getreader("utf-8")(data_file["Body"]),
            fieldnames=self.indicator_type_file_columns,
        )
        self.last_modified[file_name] = data_file["LastModified"].isoformat()
        privacy_group = file_name.split("/")[-1].split(".")[0]

        result: t.List[HashRowT] = []
        for row in data_reader:
            metadata = ThreatExchangeIndicatorIndexMetadata(
                indicator_id=row["indicator_id"],
                signal_value=row["hash"],
                privacy_group=privacy_group,
            )
            if row["tags"]:
                # note: these are the labels assigned by pytx in descriptor.py (NOT a 1-1 with tags on TE)
                metadata.tags.update(row["tags"].split(" "))

            result.append((row["hash"], [metadata]))

        return result


class ThreatExchangeS3PDQAdapter(ThreatExchangeS3Adapter):
    """
    Adapter for reading ThreatExchange PDQ data stored in CSV files S3
    """

    @property
    def indicator_type_file_extension(self):
        return f"{PdqSignal.INDICATOR_TYPE.lower()}.te"

    @property
    def indicator_type_file_columns(self):
        return ["hash", "indicator_id", "descriptor_id", "timestamp", "tags"]

    @property
    def file_type_str_name(self):
        return "PDQ"


class ThreatExchangeS3VideoMD5Adapter(ThreatExchangeS3Adapter):
    """
    Read ThreatExchange Video MD5 files in CSV from S3.
    """

    @property
    def indicator_type_file_extension(self):
        # Hardcode because of indicator_type migration. This is extra weird
        # because adapters do not write data, they only read data. One datafile
        # read and write are both done via s3_adapters, this should no longer be
        # necessary.
        return f"hash_video_md5.te"

    @property
    def indicator_type_file_columns(self):
        return ["hash", "indicator_id", "descriptor_id", "timestamp", "tags"]

    @property
    def file_type_str_name(self):
        return "MD5"


class ThreatUpdateS3Store(tu.ThreatUpdatesStore):
    """
    ThreatUpdatesStore, but stores files in S3 instead of local filesystem.
    """

    CHECKPOINT_SUFFIX = ".checkpoint"

    def __init__(
        self,
        privacy_group: int,
        app_id: int,
        s3_client: S3Client,
        s3_bucket_name: str,
        s3_te_data_folder: str,
        data_store_table: str,
        supported_signal_types: t.List[SignalType],
        signal_type_mapping: HMASignalTypeMapping,
    ) -> None:
        super().__init__(privacy_group)
        self.app_id = app_id
        self._cached_state: t.Optional[t.Dict] = None
        self.s3_te_data_folder = s3_te_data_folder
        self.data_store_table = data_store_table
        self.supported_indicator_types = self._get_supported_indicator_types(
            supported_signal_types
        )
        self.s3_client = s3_client
        self.s3_bucket_name = s3_bucket_name
        self.signal_type_mapping = signal_type_mapping

    @classmethod
    def indicator_type_str_from_signal_type(
        cls, signal_type: t.Type[SignalType]
    ) -> str:
        """
        This mapping is only necessary for types that are in the process of
        being migrated. eg. VideoMD5.
        """
        if signal_type == VideoMD5Signal:
            return "HASH_VIDEO_MD5"

        return getattr(signal_type, "INDICATOR_TYPE", None)

    def _get_supported_indicator_types(
        self, supported_signal_types: t.List[t.Type[SignalType]]
    ):
        """
        For supported self.signal_types, get their corresponding indicator_types.
        """
        indicator_types = []

        for signal_type in supported_signal_types:
            indicator_type = self.indicator_type_str_from_signal_type(signal_type)
            if indicator_type:
                indicator_types.append(indicator_type)
            else:
                warnings.warn(
                    f"SignalType: {signal_type} does not provide an indicator type."
                )

        return indicator_types

    @property
    def checkpoint_s3_key(self) -> str:
        return f"{self.s3_te_data_folder}{self.privacy_group}{self.CHECKPOINT_SUFFIX}"

    def get_privacy_group_prefix(self) -> str:
        """
        Gets the prefix for all data files for self.privacy_group. Note that the
        '.' is necessary. Otherwise for a case where privacy group ids are like
        123 and 1234, a list_objects() call for 123 will return 123 and 1234
        objects.
        """
        return f"{self.s3_te_data_folder}{self.privacy_group}."

    def get_s3_object_key(self, indicator_type) -> str:
        """
        For self.privacy_group, creates an s3_key that stores data for
        `indicator_type`. If changing, be mindful to change
        get_signal_type_from_object_key() as well.
        """
        extension = f"{indicator_type.lower()}.te"
        return f"{self.get_privacy_group_prefix()}{extension}"

    @classmethod
    def get_signal_type_from_object_key(
        cls, key: str
    ) -> t.Optional[t.Type[SignalType]]:
        """
        Inverses get_s3_object_key. Given an object key (potentially generated
        by this class), extracts the extension, compares that against known
        signal_types to see if any of them have the same indicator_type and
        returns that signal_type.
        """
        # given s3://<foo_bucket>/threat_exchange_data/258601789084078.hash_pdq.te
        # .te and everything other than hash_pdq can be ignored.
        try:
            _, extension, _ = key.rsplit(".", 2)
        except ValueError:
            # key does not meet the structure necessary. Impossible to determine
            # signal_type
            return None

        for signal_type in KNOWN_SIGNAL_TYPES:
            if signal_type.INDICATOR_TYPE.lower() == extension:
                return signal_type

        # Hardcode for HASH_VIDEO_MD5 because threatexchange's VideoMD5 still
        # has HASH_MD5 as indicator_type
        if extension == "hash_video_md5":
            return VideoMD5Signal

        return None

    @property
    def next_delta(self) -> tu.ThreatUpdatesDelta:
        """
        IF YOU CHANGE SUPPORTED_SIGNALS, OLD CHECKPOINTS NEED TO BE INVALIDATED
        TO GET THE NON-PDQ DATA!
        """
        delta = super().next_delta
        delta.types = self.supported_indicator_types
        return delta

    def reset(self):
        super().reset()
        self._cached_state = None

    def _load_checkpoint(self) -> tu.ThreatUpdateCheckpoint:
        """Load the state of the threat_updates checkpoints from state directory"""
        txt_content = read_s3_text(
            self.s3_client, self.s3_bucket_name, self.checkpoint_s3_key
        )

        if txt_content is None:
            logger.warning("No s3 checkpoint for %d. First run?", self.privacy_group)
            return tu.ThreatUpdateCheckpoint()
        checkpoint_json = json.load(txt_content)

        ret = tu.ThreatUpdateCheckpoint(
            checkpoint_json["last_fetch_time"],
            checkpoint_json["fetch_checkpoint"],
        )
        logger.info(
            "Loaded checkpoint for privacy group %d. last_fetch_time=%d fetch_checkpoint=%d",
            self.privacy_group,
            ret.last_fetch_time,
            ret.fetch_checkpoint,
        )

        return ret

    def _store_checkpoint(self, checkpoint: tu.ThreatUpdateCheckpoint) -> None:
        txt_content = io.StringIO()
        json.dump(
            {
                "last_fetch_time": checkpoint.last_fetch_time,
                "fetch_checkpoint": checkpoint.fetch_checkpoint,
            },
            txt_content,
            indent=2,
        )
        write_s3_text(
            s3_client=self.s3_client,
            bucket_name=self.s3_bucket_name,
            key=self.checkpoint_s3_key,
            txt_content=txt_content,
        )
        logger.info(
            "Stored checkpoint for privacy group %d. last_fetch_time=%d fetch_checkpoint=%d",
            self.privacy_group,
            checkpoint.last_fetch_time,
            checkpoint.fetch_checkpoint,
        )

    def _get_datafile_object_keys(self) -> t.Iterable[str]:
        """
        Returns all non-checkpoint datafile objects for the current privacy group.
        """
        return [
            item["Key"]
            for item in self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket_name, Prefix=self.get_privacy_group_prefix()
            )["Contents"]
            if not item["Key"].endswith(self.CHECKPOINT_SUFFIX)
        ]

    def load_state(self, allow_cached=True):
        if not allow_cached or self._cached_state is None:
            # First, get a list of all files
            all_datafile_keys = self._get_datafile_object_keys()

            items = []

            # Then for each datafile, append to items
            for datafile in all_datafile_keys:
                txt_content = read_s3_text(
                    self.s3_client, self.s3_bucket_name, datafile
                )
                signal_type = self.get_signal_type_from_object_key(datafile)
                indicator_type = self.indicator_type_str_from_signal_type(signal_type)

                if txt_content is None:
                    logger.warning("No TE state for %d. First run?", self.privacy_group)
                elif indicator_type is None:
                    logger.warning(
                        "Could not identify indicator type for signal with type: %s. Will not process.",
                        signal_type.get_name(),
                    )
                else:
                    csv.field_size_limit(65535)  # dodge field size problems
                    for row in csv.reader(txt_content):
                        items.append(
                            HMASerialization(
                                row[0],
                                indicator_type,
                                row[1],
                                SimpleDescriptorRollup.from_row(row[2:]),
                            )
                        )
                    logger.info("%d rows loaded for %d", len(items), self.privacy_group)

            # Do all in one assignment just in case of threads
            self._cached_state = {item.key: item for item in items}
        return self._cached_state

    def _store_state(self, contents: t.Iterable["HMASerialization"]):
        """
        Stores indicator data in CSV format with one file per indicator type.
        """
        row_by_type: t.DefaultDict = collections.defaultdict(list)
        for item in contents:
            row_by_type[item.indicator_type].append(item)
        # Discard all updates except PDQ

        for indicator_type in row_by_type:
            # Write one file per indicator type.
            items = row_by_type.get(indicator_type, [])

            with io.StringIO(newline="") as txt_content:
                writer = csv.writer(txt_content)
                writer.writerows(item.as_csv_row() for item in items)

                write_s3_text(
                    s3_client=self.s3_client,
                    bucket_name=self.s3_bucket_name,
                    key=self.get_s3_object_key(indicator_type),
                    txt_content=txt_content,
                )

                logger.info(
                    "IndicatorType:%s, %d rows stored in PrivacyGroup %d",
                    indicator_type,
                    len(items),
                    self.privacy_group,
                )

    def _apply_updates_impl(
        self,
        delta: tu.ThreatUpdatesDelta,
        post_apply_fn=lambda x: None,
    ) -> None:
        state: t.Dict = {}
        updated: t.Dict = {}
        if delta.start > 0:
            state = self.load_state()
        for update in delta:
            item = HMASerialization.from_threat_updates_json(
                self.app_id, update.raw_json
            )
            if update.should_delete:
                state.pop(item.key, None)
            else:
                state[item.key] = item
                updated[item.key] = item

        self._store_state(state.values())
        self._cached_state = state

        post_apply_fn(updated)

    def get_new_pending_opinion_change(
        self, metadata: ThreatExchangeSignalMetadata, new_tags: t.List[str]
    ):
        # Figure out if we have a new opinion about this indicator and clear out a pending change if so

        # python-threatexchange.descriptor.ThreatDescriptor.from_te_json guarentees there is either
        # 0 or 1 opinion tags on a descriptor
        opinion_tags = ThreatDescriptor.SPECIAL_TAGS
        old_opinion = [tag for tag in metadata.tags if tag in opinion_tags]
        new_opinion = [tag for tag in new_tags if tag in opinion_tags]

        # If our opinion changed or if our pending change has already happend,
        # set the pending opinion change to None, otherwise keep it unchanged
        if old_opinion != new_opinion:
            return PendingThreatExchangeOpinionChange.NONE
        elif (
            (
                new_opinion == [ThreatDescriptor.TRUE_POSITIVE]
                and metadata.pending_opinion_change
                == PendingThreatExchangeOpinionChange.MARK_TRUE_POSITIVE
            )
            or (
                new_opinion == [ThreatDescriptor.FALSE_POSITIVE]
                and metadata.pending_opinion_change
                == PendingThreatExchangeOpinionChange.MARK_FALSE_POSITIVE
            )
            or (
                new_opinion == []
                and metadata.pending_opinion_change
                == PendingThreatExchangeOpinionChange.REMOVE_OPINION
            )
        ):
            return PendingThreatExchangeOpinionChange.NONE
        else:
            return metadata.pending_opinion_change

    def post_apply(self, updated: t.Dict = {}):
        """
        After the fetcher applies an update, check for matches
        to any of the signals in data_store_table and if found update
        their tags.

        TODO: Additionally, if writebacks are enabled for this privacy group write back
        INGESTED to ThreatExchange
        """
        table = get_dynamodb().Table(self.data_store_table)

        for update in updated.values():
            row: t.List[str] = update.as_csv_row()
            # example row format: ('<raw_indicator>', '<indicator-id>', '<descriptor-id>', '<time added>', '<space-separated-tags>')
            # e.g (10736405276340','096a6f9...064f', '1234567890', '2020-07-31T18:47:45+0000', 'true_positive hma_test')
            new_tags = row[4].split(" ") if row[4] else []
            metadata = ThreatExchangeSignalMetadata.get_from_signal_and_privacy_group(
                table,
                int(row[1]),  # indicator-id or signal-id
                str(self.privacy_group),
                self.signal_type_mapping,
            )

            if metadata:
                new_pending_opinion_change = self.get_new_pending_opinion_change(
                    metadata, new_tags
                )
            else:
                # If this is a new indicator without metadata there is nothing for us to update
                return

            metadata.tags = new_tags
            metadata.pending_opinion_change = new_pending_opinion_change

            # TODO: Combine 2 update functions into single function
            if metadata.update_tags_in_table_if_exists(table):
                logger.info(
                    "Updated Signal Tags in DB for indicator id: %s source: %s for privacy group: %d",
                    row[1],
                    S3ThreatDataConfig.SOURCE_STR,
                    self.privacy_group,
                )
            if metadata.update_pending_opinion_change_in_table_if_exists(table):
                logger.info(
                    "Updated Pending Opinion in DB for indicator id: %s source: %s for privacy group: %d",
                    row[1],
                    S3ThreatDataConfig.SOURCE_STR,
                    self.privacy_group,
                )


def read_s3_text(
    s3_client: S3Client, bucket_name: str, key: str
) -> t.Optional[io.StringIO]:
    byte_content = io.BytesIO()
    try:
        s3_client.download_fileobj(bucket_name, key, byte_content)
    except ClientError as ce:
        if ce.response["Error"]["Code"] != "404":
            raise
        return None
    return io.StringIO(byte_content.getvalue().decode())


def write_s3_text(
    s3_client: S3Client, bucket_name: str, key: str, txt_content: io.StringIO
) -> None:
    byte_content = io.BytesIO(txt_content.getvalue().encode())
    s3_client.upload_fileobj(byte_content, bucket_name, key)
