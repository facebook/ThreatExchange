#!/usr/bin/env python

"""
Label command for uploading opinions (ThreatDescriptors) or reactions.
"""

import typing as t

from .. import TE
from ..collab_config import CollaborationConfig
from ..content_type import meta, text
from ..dataset import Dataset
from . import command_base


class LabelCommand(command_base.Command):
    """
    Apply labels to items in ThreatExchange.

    Examples:
      # Label text
      $ all-in-one -c te.cfg label violating_label_from_config,other_label text "this is an example bad text"

      # Label descriptor
      $ all-in-one -c te.cfg label false-positive descriptor 12345
    """

    FALSE_POSITIVE = "false_positive"

    @classmethod
    def init_argparse(cls, ap) -> None:
        ap.add_argument(
            "labels",
            type=lambda s: s.strip().split(","),
            metavar="CSV",
            help="labels to apply to item",
        )
        ap.add_argument("descriptor_id", help="the id of a descriptor to label")

    def __init__(self, descriptor_id: int, labels: t.List[str]) -> None:
        self.descriptor_id = descriptor_id
        self.labels = labels
        self.false_positive = False
        # Only use reaction logic if not also adding true positive labels
        if self.FALSE_POSITIVE in labels:
            self.labels.remove(self.FALSE_POSITIVE)
            if not self.labels:
                self.false_positive = True

    def execute(self, dataset: Dataset) -> None:
        raise NotImplementedError
        # Everything below is untested and leftover from a previous attempt
        params = {
            "descriptor_id": self.descriptor_id,
            "privacy_type": "HAS_PRIVACY_GROUP",
            "privacy_members": cfg.privacy_groups,
        }

        if self.false_positive:
            # TODO reacc
            raise NotImplementedError
        else:
            params["tags"] = self.labels
        # TODO: Handle gracefully target doesn't exist
        # TODO: Handle already labeled (merge don't stomp)
        err_message, ex, response = TE.Net.copyThreatDescriptor(
            params, showURLs=True, dryRun=False
        )
        if ex:
            raise ex
        if err_message:
            raise command_base.CommandError(err_message)
        if not response:
            raise command_base.CommandError("Mystery error - empty response")
        print(response["descriptor_id"])
