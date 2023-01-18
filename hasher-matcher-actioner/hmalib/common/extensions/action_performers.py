# Copyright (c) Meta Platforms, Inc. and affiliates.
import typing as t

from hmalib.common.messages.action import ActionMessage


class ActionPerformerExtensionBase:
    """
    This base class includes the interface for action performer impls
    provided by the extension framework. This establishes a base class to be implement in
    hmalib_extension/<custom_file> and imported via hasher-matcher-actioner/settings.py
    (see settings.py.exmaple to get started)
    """

    @classmethod
    def perform_action_impl(
        cls, message: ActionMessage, additional_kwargs: t.Dict[str, str]
    ) -> None:
        raise NotImplementedError

    @classmethod
    def get_name(cls) -> str:
        """The name of the action_performer_extension"""
        raise NotImplementedError

    @classmethod
    def get_description(cls) -> str:
        """return details of this extension"""
        return cls.__doc__ or ""
