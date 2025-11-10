# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
A development version of an omm_config, with every field visible and commented.

This is the configuration that is used by default for the developer instance
which runs in the dev container by default. Every config field is present
to make it easier to copy the file as a template for others.
"""

from logging.config import dictConfig

from OpenMediaMatch.storage.postgres.impl import DefaultOMMStore
from OpenMediaMatch.utils.fetch_benchmarking import InfiniteRandomExchange
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
DBHOST = "db"
DBNAME = "media_match"
DATABASE_URI = f"postgresql+psycopg2://{DBUSER}:{DBPASS}@{DBHOST}/{DBNAME}"

# Role configuration
PRODUCTION = False
ROLE_HASHER = True
ROLE_MATCHER = True
ROLE_CURATOR = True
UI_ENABLED = True
# APScheduler (background threads for development)
TASK_FETCHER = True
TASK_INDEXER = True
TASK_INDEX_CACHE = True

# Optional: configure background task intervals (in seconds)
# Defaults: fetcher=240, indexer=60, index cache refresh=30
TASK_FETCHER_INTERVAL_SECONDS = 60 * 4
TASK_INDEXER_INTERVAL_SECONDS = 60
TASK_INDEX_CACHE_INTERVAL_SECONDS = 30
MAX_REMOTE_FILE_SIZE = 100 * 1024 * 1024  # 100MB max file size

# Core functionality configuration
STORAGE_IFACE_INSTANCE = DefaultOMMStore(
    signal_types=[PdqSignal, VideoMD5Signal],
    content_types=[PhotoContent, VideoContent],
    exchange_types=[
        StaticSampleSignalExchangeAPI,
        InfiniteRandomExchange,  # type: ignore
        FBThreatExchangeSignalExchangeAPI,  # type: ignore
        NCMECSignalExchangeAPI,  # type: ignore
        StopNCIISignalExchangeAPI,
    ],
)

# Debugging stuff
# SQLALCHEMY_ENGINE_LOG_LEVEL = logging.INFO

# URL validation configuration
# ALLOWED_HOSTNAMES = {
#     'example.com',
#     'cdn.example.com',
#     'media.example.com'
# }
# Note: When ALLOWED_HOSTNAMES is not set or empty, all hostnames are allowed

# We always want some logging by default, otherwise it's hard to tell whats happening inside the container:
dictConfig(
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


# If you need to add something to the Flask app, the following hook function can
# be used. Note that adding functionality may or may not prevent the UI from
# working, especially if authentication requirements are added to the API.
def on_flask_ready(app):
    app.logger.info("Flask app is ready!")


# If you aren't doing anything with the Flask `app`, this can be removed.
APP_HOOK = on_flask_ready
