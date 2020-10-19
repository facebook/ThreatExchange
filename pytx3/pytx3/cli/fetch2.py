#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import requests
import typing as t
from .. import TE
from ..dataset import Dataset
from . import command_base

class Fetch2Command(command_base.Command):
    """
    Download content from ThreatExchange to disk.

    Using the CollaborationConfig, identify ThreatPrivacyGroup that
    corresponds to a single collaboration and fetch related threat updates.
    """

    @classmethod
    def init_argparse(cls, ap) -> None:
        ap.add_argument(
            "--start-time",
            type=int,
            help="Fetch updates that occured on or after this timestamp",
        )
        ap.add_argument(
            "--stop-time",
            type=int,
            help="Fetch updates that occured before this timestamp",
        )
        ap.add_argument(
            "--owner",
            type=int,
            help="Only fetch updates for indicators that the given app has a descriptor for",
        )
        ap.add_argument(
            "--threat-types",
            type=t.List[str],
            help="Only fetch updates for indicators of the given type",
        )
        ap.add_argument(
            "--additional-tags",
            type=t.List[str],
            help="Only fetch updates for indicators that have a descriptor with each of these tags",
        )

    def __init__(
        self,
        start_time: int,
        stop_time: int,
        owner: int,
        threat_types: t.List[str],
        additional_tags: t.List[str],
    ) -> None:
        self.start_time = start_time
        self.stop_time = stop_time
        self.owner = owner
        self.threat_types = threat_types
        self.additional_tags = additional_tags
