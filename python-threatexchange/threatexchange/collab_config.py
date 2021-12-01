#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

"""
A wrapper around the collaboration config file.

This file controls the behavior of the all-in-one command, and roughly
corresponds to a single-signal sharing usecase.
"""

import json
import re
import typing as t

from . import descriptor


class CollaborationConfig:

    KEY_NAME = "name"
    KEY_PRIVACY_GROUPS = "privacy_groups"
    KEY_LABELS = "labels"
    KEY_SAMPLE_TAG = "sample_tag"

    def __init__(
        self,
        name: str,
        labels: t.Dict[str, t.Any],
        privacy_groups: t.List[int],
        sample_tag: t.Optional[str] = None,
        show_safe_list=False,  # (safe_list == signals only listed as NON_MALICIOUS, e.g. sample data)
    ):
        self.name = name
        self.privacy_groups = privacy_groups
        self.labels = labels
        self.sample_tag = sample_tag
        self.show_safe_list = show_safe_list

    @property
    def default_state_dir_name(self) -> str:
        return re.sub("\W+", "_", self.name.lower())

    @property
    def labels_for_collaboration(self) -> t.Set[str]:
        ret = set(self.labels)
        ret.update(descriptor.ThreatDescriptor.SPECIAL_TAGS)
        return ret

    @classmethod
    def load(cls, file: t.IO):
        content = json.load(file)
        return cls(
            content.get(cls.KEY_NAME, "Sample Config"),
            content[cls.KEY_LABELS],
            content.get(cls.KEY_PRIVACY_GROUPS, []),
            content.get(cls.KEY_SAMPLE_TAG),
        )

    def store(self, filename: str):
        with open(filename, "w") as f:
            out = {
                self.KEY_NAME: self.name,
                self.KEY_LABELS: self.labels,
                self.KEY_PRIVACY_GROUPS: self.privacy_groups,
            }
            if self.sample_tag:
                out[self.KEY_SAMPLE_TAG] = self.sample_tag
            json.dump(out, f, indent=4)

    @classmethod
    def get_example_config(cls) -> "CollaborationConfig":
        """
        Get a config to access the public sample data under media_priority_samples
        """
        return cls(
            name="ThreatExchange Samples",
            labels={"media_priority_samples": {}},
            privacy_groups=[],
            sample_tag="media_priority_samples",
            show_safe_list=True,  # Show sample data (lone NON_MALICIOUS descriptors)
        )
