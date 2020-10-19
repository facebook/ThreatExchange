#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import requests
import json
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

    FIELDS = 'id,indicator,type,creation_time,last_updated,is_expired,expire_time,tags,status,applications_with_opinions'

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
            nargs="+",
            help="Only fetch updates for indicators of the given type",
        )
        ap.add_argument(
            "--additional-tags",
            nargs="+",
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

    def execute(self, dataset: Dataset) -> None:
        self._fetch_threat_updates(
            dataset.config.privacy_groups[0],
            self.start_time,
            self.stop_time,
            self.owner,
            self.threat_types,
            self.additional_tags
        )

    def _fetch_threat_updates(
        self,
        privacy_group: int,
        start_time: int,
        stop_time: int,
        owner: int,
        threat_types: t.List[str],
        additional_tags: t.List[str],
    ) -> None:
        params={'access_token': TE.Net.APP_TOKEN, 'fields': self.FIELDS}
        if start_time is not None:
            params['start_time'] = start_time
        if stop_time is not None:
            params['stop_time'] = stop_time
        if owner is not None:
            params['owner'] = owner
        if threat_types is not None:
            params['threat_types'] = threat_types
        if additional_tags is not None:
            params['additional_tags'] = additional_tags

        result = requests.get(
            url=(
                TE.Net.TE_BASE_URL + '/'
                + str(privacy_group)
                + '/threat_updates'
            ),
            params=params,
        )

        print(json.dumps(result.json(), indent=2))
