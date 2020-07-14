##!/usr/bin/env python

"""
A wrapper around the collaboration config file.

This file controls the behavior of the all-in-one command, and roughly
corresponds to a single signal sharing usecase.
"""

import json
import re
import typing as t


class CollaborationConfig:

    KEY_NAME = "name"
    KEY_PRIVACY_GROUPS = "privacy_groups"
    KEY_LABELS = "labels"
    KEY_CONTENT_TYPES = "content_types"

    def __init__(
        self,
        name: str,
        labels: t.Dict[str, t.Any],
        privacy_groups: t.List[int],
        content_types: t.Dict[str, t.Dict[str, t.Any]],
    ):
        self.name = name
        self.privacy_groups = privacy_groups
        self.labels = labels
        self.content_types = content_types

    @property
    def default_state_dir_name(self) -> str:
        return re.sub("\W+", "_", self.name.lower())

    @classmethod
    def load(cls, file: t.IO):
        content = json.load(file)
        return cls(
            content[cls.KEY_NAME],
            content[cls.KEY_LABELS],
            content[cls.KEY_PRIVACY_GROUPS],
            content[cls.KEY_CONTENT_TYPES],
        )

    def store(self, filename: str):
        with open(filename, "w") as f:
            json.dump(
                {
                    self.KEY_NAME: self.name,
                    self.KEY_LABELS: self.labels,
                    self.KEY_PRIVACY_GROUPS: self.privacy_groups,
                    self.KEY_CONTENT_TYPES: self.content_types,
                },
                f,
                indent=4,
            )
