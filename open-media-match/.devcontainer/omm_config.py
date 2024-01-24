# Copyright (c) Meta Platforms, Inc. and affiliates.

# This is the configuration that is used by default for the developer instance
# which runs in the dev container by default. Every config field is present
# to make it easier to copy this
import logging

from OpenMediaMatch.storage.postgres.impl import DefaultOMMStore
from OpenMediaMatch.utils.fetch_benchmarking import InfiniteRandomExchange
from threatexchange.signal_type.pdq.signal import PdqSignal
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.content_type.photo import PhotoContent
from threatexchange.content_type.video import VideoContent
from threatexchange.exchanges.impl.static_sample import StaticSampleSignalExchangeAPI
from threatexchange.exchanges.impl.fb_threatexchange_api import (
    FBThreatExchangeSignalExchangeAPI,
)

# Database configuration
DBUSER = "media_match"
DBPASS = "hunter2"
DBHOST = "localhost"
DBNAME = "media_match"
DATABASE_URI = f"postgresql+psycopg2://{DBUSER}:{DBPASS}@{DBHOST}/{DBNAME}"

# Role configuration
PRODUCTION = False
ROLE_HASHER = True
ROLE_MATCHER = True
ROLE_CURATOR = True
# APScheduler (background threads for development)
TASK_FETCHER = True
TASK_INDEXER = True
TASK_INDEX_CACHE = False  # Needs a fix to allow initial startup

# Core functionality configuration
STORAGE_IFACE_INSTANCE = DefaultOMMStore(
    signal_types=[PdqSignal, VideoMD5Signal],
    content_types=[PhotoContent, VideoContent],
    exchange_types=[
        StaticSampleSignalExchangeAPI,
        InfiniteRandomExchange,
        FBThreatExchangeSignalExchangeAPI,
    ],
)

# Debugging stuff
# SQLALCHEMY_ENGINE_LOG_LEVEL = logging.INFO
