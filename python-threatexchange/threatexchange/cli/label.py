#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
Label command for uploading opinions (ThreatDescriptors) or reactions.
"""

import typing as t

from .. import descriptor
from ..api import ThreatExchangeAPI
from ..collab_config import CollaborationConfig
from ..content_type import meta, text
from ..dataset import Dataset
from . import command_base


class LabelCommand(command_base.Command):
    """
    Apply labels to items in ThreatExchange.

    Labeling descriptors as false_positive will cause them to stop triggering
    matches by default in the match command.

    Examples:
      # Label descriptor
      $> threatexchange -c te.cfg label false_positive,other_label descriptor 12345
    """

    @classmethod
    def init_argparse(cls, ap) -> None:
        ap.add_argument(
            "labels",
            type=lambda s: s.strip().split(","),
            metavar="CSV",
            help="labels to apply to item",
        )

        # TODO - Put the match command content logic in a common place, re-use it
        ap.add_argument(
            "content_type", choices=["descriptor"], help="what kind of content to label"
        )
        ap.add_argument("content", help="the content to label")

    def __init__(self, content_type: str, content: str, labels: t.List[str]) -> None:
        if content_type == "descriptor":
            self.descriptor_id = content

        # Remove any of the special tags that someone included for whatever reason
        self.labels = [
            l for l in labels if l not in descriptor.ThreatDescriptor.SPECIAL_TAGS
        ]
        self.false_positive_reaction = False
        # Only use reaction logic if not also adding true positive labels
        if descriptor.ThreatDescriptor.FALSE_POSITIVE in labels and not self.labels:
            self.false_positive_reaction = True

    def execute(self, api: ThreatExchangeAPI, dataset: Dataset) -> None:
        if not self.false_positive_reaction:
            raise NotImplementedError
        err_message, ex, response = api.react_to_threat_descriptor(
            self.descriptor_id, "DISAGREE_WITH_TAGS"
        )
        if ex:
            raise ex
        if err_message:
            raise command_base.CommandError(err_message)
        if not response or response.get("success", "true") == "false":
            raise command_base.CommandError(
                f"Mystery error - response says: {response}"
            )
