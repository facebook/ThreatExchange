# Copyright (c) Meta Platforms, Inc. and affiliates.

import typing as t

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

from hmalib.scripts.migrations.migrations_base import MigrationBase


class _Migration(MigrationBase):
    def do_migrate(self):
        create_config(
            ToggleableContentTypeConfig(
                name=ToggleableContentTypeConfig.get_name_from_type(VideoContent),
                content_type_class=full_class_name(VideoContent),
                enabled=True,
            )
        )

        create_config(
            ToggleableContentTypeConfig(
                name=ToggleableContentTypeConfig.get_name_from_type(PhotoContent),
                content_type_class=full_class_name(PhotoContent),
                enabled=True,
            )
        )

        create_config(
            ToggleableSignalTypeConfig(
                name=ToggleableSignalTypeConfig.get_name_from_type(VideoMD5Signal),
                signal_type_class=full_class_name(VideoMD5Signal),
                enabled=True,
            )
        )

        create_config(
            ToggleableSignalTypeConfig(
                name=ToggleableSignalTypeConfig.get_name_from_type(PdqSignal),
                signal_type_class=full_class_name(PdqSignal),
                enabled=True,
            )
        )
