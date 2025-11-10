# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
A production-ish OMM config, for the hasher role.

See the top-level README.md for an explanation of roles.

You only need a hasher role if you are not doing hashing on the instances
of your service that are handling the content uploads, which can save on
transmission costs at the expense of CPU cost on your frontend.

A common pattern is to use a queue external to OMM to build up items to be
hashed and checked, in which case a hasher role might be your largest tier,
since converting large content like videos can take a significant amount of
CPU.
"""

import os

# Database configuration
DBUSER = os.environ.get("POSTGRES_USER", "media_match")
DBPASS = os.environ.get("POSTGRES_PASSWORD", "hunter2")
DBHOST = os.environ.get("POSTGRES_HOST", os.environ.get("POSTGRESS_HOST", "db"))
DBNAME = os.environ.get("POSTGRES_DBNAME", os.environ.get("POSTGRESS_DBNAME", "media_match"))
DATABASE_URI = f"postgresql+psycopg2://{DBUSER}:{DBPASS}@{DBHOST}/{DBNAME}"

# Role configuration
PRODUCTION = True
ROLE_HASHER = True
