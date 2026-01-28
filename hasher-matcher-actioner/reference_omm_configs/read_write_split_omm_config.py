# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Example OMM configuration with read/write database separation.

This demonstrates separate database connections for read and write operations.
Useful for load balancing reads across replicas while writes go to primary.
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

# Database configuration
DBUSER = "media_match"
DBPASS = "hunter2"
DBNAME = "media_match"

# Primary database (writes)
DATABASE_URI = f"postgresql+psycopg2://{DBUSER}:{DBPASS}@db-primary/{DBNAME}"

# Read replica (reads) - optional, falls back to primary if not set
DATABASE_READ_URI = f"postgresql+psycopg2://{DBUSER}:{DBPASS}@db-replica/{DBNAME}"

# Role configuration
PRODUCTION = True
ROLE_HASHER = True
ROLE_MATCHER = True
ROLE_CURATOR = True
UI_ENABLED = True

# Background tasks
TASK_FETCHER = True
TASK_INDEXER = True
TASK_INDEX_CACHE = True

# Core functionality
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

# Logging
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
