# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import typing as t


from hmalib.common.messages.action import ActionMessage
from hmalib.common.extensions.action_performers import ActionPerformerExtensionBase


class ActionPerformerExtensionExample(ActionPerformerExtensionBase):
    """
    Example implementation of an actioner extension
    This example expects one of the keyword args to be "defined_keyword_arg"
    It prints that argument along with the other optional kwargs and the
    additional_fields on the action message.
    """

    @classmethod
    def perform_action_impl(
        cls, message: ActionMessage, additional_kwargs: t.Dict[str, str]
    ) -> None:
        cls._custom_actioner(message, **additional_kwargs)

    @classmethod
    def get_name(cls) -> str:
        return "ap_example_1"

    @classmethod
    def get_description(cls) -> str:
        """return details of this extension"""
        return cls.__doc__ or ""

    @staticmethod
    def _custom_actioner(message: ActionMessage, defined_keyword_arg, **kwargs):
        """Example method use could use to test basic hma_extension support"""
        print(message.additional_fields)
        print(defined_keyword_arg)
        print(kwargs)
