# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Example OMM configuration with read/write database separation.

This configuration demonstrates how to set up separate database connections
for read and write operations, which is useful for:
- Load balancing across read replicas
- Reducing load on the primary database
- Improving read performance by distributing queries
- Supporting database replication architectures

IMPORTANT: The read replica must be in sync with the primary database.
Replication lag can cause inconsistencies if not properly managed.
"""

from logging.config import dictConfig

from OpenMediaMatch.storage.postgres.impl import DefaultOMMStore
from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.content_type.photo import PhotoContent
from threatexchange.content_type.video import VideoContent
from threatexchange.exchanges.impl.static_sample import StaticSampleSignalExchangeAPI
from threatexchange.exchanges.impl.ncmec_api import NCMECSignalExchangeAPI
from threatexchange.exchanges.impl.stop_ncii_api import StopNCIISignalExchangeAPI
from threatexchange.exchanges.impl.fb_threatexchange_api import (
    FBThreatExchangeSignalExchangeAPI,
)

# Database configuration - Write database (primary)
DBUSER = "media_match"
DBPASS = "hunter2"
DBHOST = "db-primary"  # Primary database hostname
DBNAME = "media_match"
DATABASE_URI = f"postgresql+psycopg2://{DBUSER}:{DBPASS}@{DBHOST}/{DBNAME}"

# Read database configuration (read replica)
# This can point to a read replica, read-only replica, or load balancer
# in front of multiple read replicas
READ_DBHOST = "db-replica"  # Read replica hostname or load balancer
DATABASE_READ_URI = f"postgresql+psycopg2://{DBUSER}:{DBPASS}@{READ_DBHOST}/{DBNAME}"

# Alternative configurations:
# 
# 1. Using environment variables for sensitive data:
# import os
# DATABASE_URI = os.getenv("DATABASE_WRITE_URI", "postgresql://...")
# DATABASE_READ_URI = os.getenv("DATABASE_READ_URI", "postgresql://...")
#
# 2. Using the same database for both (no read/write split):
# DATABASE_URI = "postgresql://..."
# # DATABASE_READ_URI is not set, so all operations use DATABASE_URI
#
# 3. Using a connection pooler like PgBouncer:
# DATABASE_URI = "postgresql://...@pgbouncer:6432/..."
# DATABASE_READ_URI = "postgresql://...@pgbouncer-readonly:6432/..."

# Role configuration
PRODUCTION = True
ROLE_HASHER = True
ROLE_MATCHER = True
ROLE_CURATOR = True
UI_ENABLED = True

# Background tasks configuration
# In a read/write split setup, you may want to run these on dedicated instances
TASK_FETCHER = True  # This writes to the database
TASK_INDEXER = True  # This writes to the database
TASK_INDEX_CACHE = True  # This reads from the database

# Task intervals (in seconds)
TASK_FETCHER_INTERVAL_SECONDS = 60 * 4  # 4 minutes
TASK_INDEXER_INTERVAL_SECONDS = 60  # 1 minute
TASK_INDEX_CACHE_INTERVAL_SECONDS = 30  # 30 seconds

MAX_REMOTE_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Core functionality configuration
STORAGE_IFACE_INSTANCE = DefaultOMMStore(
    signal_types=[PdqSignal, VideoMD5Signal],
    content_types=[PhotoContent, VideoContent],
    exchange_types=[
        StaticSampleSignalExchangeAPI,
        FBThreatExchangeSignalExchangeAPI,  # type: ignore
        NCMECSignalExchangeAPI,  # type: ignore
        StopNCIISignalExchangeAPI,
    ],
)

# Logging configuration
FLASK_LOGGING_CONFIG = dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default",
            }
        },
        "root": {"level": "INFO", "handlers": ["wsgi"]},
    }
)


def on_flask_ready(app):
    """
    Hook called when Flask app is ready.
    
    In a read/write split configuration, you might want to:
    - Validate database connectivity to both primary and replica
    - Check replication lag
    - Set up monitoring for database health
    """
    app.logger.info("Flask app is ready with read/write database separation!")
    
    # Log database configuration (without sensitive info)
    if 'DATABASE_READ_URI' in app.config:
        app.logger.info("Read/write database separation is ENABLED")
    else:
        app.logger.info("Read/write database separation is DISABLED (using single database)")


APP_HOOK = on_flask_ready

