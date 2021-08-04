# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import os
from urllib.parse import unquote_plus
import boto3
import typing as t
from dataclasses import dataclass, field

from hmalib.common.classification_models import (
    BankedContentIDClassificationLabel,
    BankIDClassificationLabel,
    BankSourceClassificationLabel,
    ClassificationLabel,
    Label,
    WritebackTypes,
    PendingOpinionChange,
)
from hmalib.common.evaluator_models import ActionLabel, ActionRule
from hmalib.common.content_models import ContentObject
from hmalib.common.aws_dataclass import HasAWSSerialization
from hmalib.common.image_sources import S3BucketImageSource
from hmalib.common.logging import get_logger

from mypy_boto3_sqs import SQSClient
from functools import lru_cache

logger = get_logger(__name__)


@dataclass
class BankedSignal:
    """
    BankedSignal fields:
    - `banked_content_id`: Inside the bank, the unique way to refer to what
      was matched against
    - `bank_id`: The unique way to refer to the bank banked_content_id came from
    - `bank_source`: This is forward looking: this might be 'te' or 'local';
      indicates source of or relationship between one or more banks
    - `classifications`: a set of labels that provide context about the banked
       signal
    """

    banked_content_id: str
    bank_id: str
    bank_source: str
    classifications: t.Set[Label] = field(default_factory=set)

    def add_bank_classifications(self):
        self.classifications.add(BankSourceClassificationLabel(self.bank_source))
        self.classifications.add(BankIDClassificationLabel(self.bank_id))
        self.classifications.add(
            BankedContentIDClassificationLabel(self.banked_content_id)
        )

    def add_classification(self, classification: str):
        if len(self.classifications) == 0:
            self.add_bank_classifications()
        self.classifications.add(ClassificationLabel(classification))


@dataclass
class MatchMessage(HasAWSSerialization):
    """
    Captures a set of matches that will need to be processed. We create one
    match message for a single content key. It is possible that a single content
    hash matches multiple datasets. When it does, the entire set of matches are
    forwarded together so that any appropriate action can be taken.

    - `content_key`: A way for partners to refer uniquely to content on their
      site
    - `content_hash`: The hash generated for the content_key
    """

    content_key: str
    content_hash: str
    matching_banked_signals: t.List[BankedSignal] = field(default_factory=list)


@dataclass
class ActionMessage(MatchMessage):
    """
    The action performer needs the match message plus which action to perform
    """

    action_label: ActionLabel = ActionLabel("UnspecifiedAction")
    action_rules: t.List[ActionRule] = field(default_factory=list)

    # from content
    additional_fields: t.List[str] = field(default_factory=list)

    @classmethod
    def from_match_message_action_label_action_rules_and_additional_fields(
        cls,
        match_message: MatchMessage,
        action_label: ActionLabel,
        action_rules: t.List[ActionRule],
        additional_fields=t.List[str],
    ) -> "ActionMessage":
        return cls(
            match_message.content_key,
            match_message.content_hash,
            match_message.matching_banked_signals,
            action_label,
            action_rules,
            additional_fields,
        )


@dataclass
class WritebackMessageConfig:
    """
    Simple holder for getting typed environment variables
    """

    writebacks_queue_url: str
    sqs_client: SQSClient

    @classmethod
    @lru_cache(maxsize=None)
    def get(cls):
        return cls(
            writebacks_queue_url=os.environ["WRITEBACKS_QUEUE_URL"],
            sqs_client=boto3.client("sqs"),
        )


@dataclass
class WritebackMessage(HasAWSSerialization):
    """
    Writebacks happen on a collection of BankedSignals. To perform a write back,
    instantiate an instacne of this class and run the send_to_queue method

    The Writebacker needs the match message plus which writeback type to perfrom
    on the source of the signal (for now, ThreatExchange).
    """

    banked_signals: t.List[BankedSignal]

    writeback_type: WritebackTypes.WritebackType = field(
        default=WritebackTypes.NoWriteback
    )

    @classmethod
    def from_match_message_and_type(
        cls,
        match_message: MatchMessage,
        writeback_type: WritebackTypes.WritebackType,
    ) -> "WritebackMessage":
        return cls(
            match_message.matching_banked_signals,
            writeback_type,
        )

    @classmethod
    def from_banked_signal_and_opinion_change(
        cls, banked_signal: BankedSignal, opinion_change: PendingOpinionChange
    ) -> "WritebackMessage":
        opinion_change_to_writeback_type = {
            PendingOpinionChange.MARK_TRUE_POSITIVE: WritebackTypes.TruePositive,
            PendingOpinionChange.MARK_FALSE_POSITIVE: WritebackTypes.FalsePositive,
            PendingOpinionChange.REMOVE_OPINION: WritebackTypes.RemoveOpinion,
        }

        writeback_type = opinion_change_to_writeback_type.get(
            opinion_change, WritebackTypes.NoWriteback
        )

        return cls(
            [banked_signal],
            writeback_type,
        )

    def send_to_queue(self) -> None:
        if self.writeback_type == WritebackTypes.NoWriteback:
            return

        config = WritebackMessageConfig.get()
        config.sqs_client.send_message(
            QueueUrl=config.writebacks_queue_url,
            MessageBody=self.to_aws_json(),
        )


@dataclass
class URLImageSubmissionMessage:
    """
    An image has been submitted using a URL. Used by submission API lambda and
    hasher lambdas to communicate via SNS / SQS.
    """

    content_id: str
    url: str

    # Used to distinguish these messages from S3 Upload events. Leave it alone
    # if you don't know what you are doing.
    event_type: str = "URLImageSubmission"

    def to_sqs_message(self) -> dict:
        return {
            "EventType": self.event_type,
            "URL": self.url,
            "ContentId": self.content_id,
        }

    @classmethod
    def from_sqs_message(cls, d: dict) -> "URLImageSubmissionMessage":
        return cls(content_id=d["ContentId"], url=d["URL"], event_type=d["EventType"])

    @classmethod
    def could_be(cls, d: dict) -> bool:
        """
        Convenience method. Returns True if `d` can be converted to a
        URLImageSubmissionMessage.
        """
        return "EventType" in d


@dataclass
class S3ImageSubmission:
    """
    S3 -> SNS batches events together. This represents one of the events. An
    `S3ImageSubmissionBatchMessage` event is emitted. Each batch has one or more
    of these objects.
    """

    content_id: str
    bucket: str
    key: str


@dataclass
class S3ImageSubmissionBatchMessage:
    """
    An image has been uploaded to S3 from the Submission API. An autogenerated
    event has been emitted by S3 to SNS. This converts that into a set of
    messages each representing one image and its content id based on convention
    used by the submission lambda.

    eg. If the s3 path structure convention were to change, you'd make changes
    in the submission API and here, but not need to make changes in any of the
    hasher lambdas.
    """

    image_submissions: t.List[S3ImageSubmission]

    @classmethod
    def from_sqs_message(
        cls, d: dict, image_prefix: str
    ) -> "S3ImageSubmissionBatchMessage":
        result = []

        for s3_record in d["Records"]:
            bucket_name = s3_record["s3"]["bucket"]["name"]
            key = unquote_plus(s3_record["s3"]["object"]["key"])

            # Ignore Folders and Empty Files
            if s3_record["s3"]["object"]["size"] == 0:
                logger.info("Disregarding empty file or directory: %s", key)
                continue

            content_id = S3BucketImageSource.get_content_id_from_s3_key(
                key, image_prefix
            )
            result.append(S3ImageSubmission(content_id, bucket_name, key))

        return cls(image_submissions=result)

    @classmethod
    def could_be(cls, d: dict) -> bool:
        """
        Convenience mthod. Returns true if `d` can be converted to an
        S3ImageSubmissionBatchMessage.
        """
        return "Records" in d and len(d["Records"]) > 0 and "s3" in d["Records"][0]
