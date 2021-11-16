# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import typing as t

from hmalib.common.extensions.action_performers import ActionPerformerExtensionBase


def load_actioner_performer_extension(
    name: str,
) -> t.Optional[ActionPerformerExtensionBase]:
    try:
        from settings import CUSTOM_ACTION_PERFORMERS

        return CUSTOM_ACTION_PERFORMERS.get(name)
    except:
        return None
