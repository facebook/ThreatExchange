# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
A production-ish role, which only holds the background jobs.

If you are using celery that could replace the need for a dedicated instance
for this.

If your infrastructure has a more straightforward
way of running cron-like jobs, you can easily replace this role with a call
to the flask CLI with the appropriate task.
"""

import os

# Database configuration
DBUSER = os.environ.get("POSTGRES_USER", "media_match")
DBPASS = os.environ.get("POSTGRES_PASSWORD", "hunter2")
DBHOST = os.environ.get("POSTGRES_HOST", os.environ.get("POSTGRESS_HOST", "db"))
DBNAME = os.environ.get(
    "POSTGRES_DBNAME", os.environ.get("POSTGRESS_DBNAME", "media_match")
)
DATABASE_URI = f"postgresql+psycopg2://{DBUSER}:{DBPASS}@{DBHOST}/{DBNAME}"

# Role configuration
PRODUCTION = True

# APScheduler
TASK_FETCHER = True
TASK_INDEXER = True
# Optional: configure background task intervals (in seconds)
# Defaults: fetcher=240, indexer=60
TASK_FETCHER_INTERVAL_SECONDS = 60 * 4
TASK_INDEXER_INTERVAL_SECONDS = 60
