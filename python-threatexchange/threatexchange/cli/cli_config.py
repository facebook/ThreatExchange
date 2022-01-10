# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import typing as t
import pathlib
import os

from threatexchange.collab_config import CollaborationConfig

"""
Local storage and configuration for the CLI.

The CLI and Hasher-Matcher-Actioner are roughly parallel, but this isn't a 
scalable service running on AWS. Instead, we have all of our state in
a file (likely ~/.threatexchange)
"""

FETCH_STATE_DIR_NAME = "fetched_state"
COLLABORATION_CONFIG_DIR_NAME = "collaborations"
INDEX_STATE_DIR_NAME = "index"
CONFIG_FILENAME = "config.json"


class CliState:
    """
    A wrapper around stateful information stored for the CLI.

    Everything is just in a single file (usually ~/.threatexchange).
    """

    def __init__(self, dir: pathlib.Path):
        assert dir.is_file
        self._dir = dir

    def get_collab_by_name(self, name: str) -> t.Optional[CollaborationConfig]:
        """
        Gets only a single stored collaboration config by its given name.
        """
        return None

    def update_collab(self, collab: CollaborationConfig) -> None:
        """Create or update a collaboration"""
        pass

    def delete_collab(self, name: str) -> None:
        """Delete a collaboration"""
        pass

    def get_all_collabs(self) -> t.List[CollaborationConfig]:
        """Get all collaborations"""
        return []
