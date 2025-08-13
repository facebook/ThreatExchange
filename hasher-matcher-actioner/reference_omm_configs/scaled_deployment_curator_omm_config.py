# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
A production-ish OMM config, for the curator role.

The curator role only gets internal traffic, and so you can probably
get away with a single instance for a long time.
"""

import os


# Database configuration
DBUSER = os.environ.get("POSTGRES_USER", "media_match")
DBPASS = os.environ.get("POSTGRES_PASSWORD", "hunter2")
DBHOST = os.environ.get("POSTGRESS_HOST", "db")
DBNAME = os.environ.get("POSTGRESS_DBNAME", "media_match")
DATABASE_URI = f"postgresql+psycopg2://{DBUSER}:{DBPASS}@{DBHOST}/{DBNAME}"

# Role configuration
PRODUCTION = True
ROLE_CURATOR = True
UI_ENABLED = True
