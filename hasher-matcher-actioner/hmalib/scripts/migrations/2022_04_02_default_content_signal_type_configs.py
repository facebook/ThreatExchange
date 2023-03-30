# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t

from botocore.exceptions import ClientError
from threatexchange.content_type.photo import PhotoContent
from threatexchange.content_type.video import VideoContent
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.pdq import PdqSignal

from hmalib.common.config import HMAConfig, create_config
from hmalib.common.mappings import (
    ToggleableContentTypeConfig,
    ToggleableSignalTypeConfig,
    full_class_name,
)
from hmalib.common.logging import get_logger
from hmalib.scripts.migrations.migrations_base import MigrationBase

logger = get_logger(__name__)


class _Migration(MigrationBase):
    def do_migrate(self):
        """
        Loads default core interfaces and extensions:
            1. ContentTypes (Photo, Video)
            2. SignalTypes (PDQ, vMD5)
        """
        try:
            create_config(
                ToggleableContentTypeConfig(
                    name=ToggleableContentTypeConfig.get_name_from_type(VideoContent),
                    content_type_class=full_class_name(VideoContent),
                    enabled=True,
                )
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                logger.warning(
                    "Attempted to add ToggleableContentTypeConfig for VideoContent, but it already exists."
                )
            else:
                raise e
        try:
            create_config(
                ToggleableContentTypeConfig(
                    name=ToggleableContentTypeConfig.get_name_from_type(PhotoContent),
                    content_type_class=full_class_name(PhotoContent),
                    enabled=True,
                )
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                logger.warning(
                    "Attempted to add ToggleableContentTypeConfig for PhotoContent, but it already exists."
                )
            else:
                raise e
        try:
            create_config(
                ToggleableSignalTypeConfig(
                    name=ToggleableSignalTypeConfig.get_name_from_type(VideoMD5Signal),
                    signal_type_class=full_class_name(VideoMD5Signal),
                    enabled=True,
                )
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                logger.warning(
                    "Attempted to add ToggleableSignalTypeConfig for VideoMD5Signal, but it already exists."
                )
            else:
                raise e
        try:
            create_config(
                ToggleableSignalTypeConfig(
                    name=ToggleableSignalTypeConfig.get_name_from_type(PdqSignal),
                    signal_type_class=full_class_name(PdqSignal),
                    enabled=True,
                )
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                logger.warning(
                    "Attempted to add ToggleableSignalTypeConfig for PdqSignal, but it already exists."
                )
            else:
                raise e
