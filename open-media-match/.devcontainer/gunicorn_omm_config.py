# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
A production - looking OMM config.


This is meant to demonstrate the differences between the development and
prod versions
"""

from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal

# Database configuration
PRODUCTION = False
DBUSER = "media_match"
DBPASS = "hunter2"
DBHOST = "localhost"
DBNAME = "media_match"
DATABASE_URI = f"postgresql+psycopg2://{DBUSER}:{DBPASS}@{DBHOST}/{DBNAME}"

# Role configuration
ROLE_HASHER = False
ROLE_MATCHER = False
ROLE_CURATOR = True

# Installed SignalTypes
SIGNAL_TYPES = [PdqSignal, VideoMD5Signal]
