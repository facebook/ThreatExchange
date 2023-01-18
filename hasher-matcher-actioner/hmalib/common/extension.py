# Copyright (c) Meta Platforms, Inc. and affiliates.
import typing as t
import importlib

from hmalib.common.extensions.action_performers import ActionPerformerExtensionBase


def load_actioner_performer_extension(
    name: str,
) -> t.Optional[t.Type[ActionPerformerExtensionBase]]:
    try:
        from settings import CUSTOM_ACTION_PERFORMERS  # type: ignore # possible settings.py is not found

        return CUSTOM_ACTION_PERFORMERS.get(name)
    except:
        return None
