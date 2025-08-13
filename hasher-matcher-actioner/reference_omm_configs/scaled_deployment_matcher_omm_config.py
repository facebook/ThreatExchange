# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
A production-ish OMM config, for the matcher role.

The matcher needs the more complex task for syncing the up-to-date indices.

If you are doing hashing on your webservers to save data transmission costs,
then this will be the largest pool of instances.
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
ROLE_MATCHER = True
## For smaller deployments, enabling the hasher role
## will allow you to combine the Hash+Lookup
ROLE_HASHER = False

# Background tasks configuration
TASK_INDEX_CACHE = True
