# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Minimal OMM_CONFIG used only when generating the OpenAPI spec.

This config is intentionally not wired to a live Postgres database. Blueprint
registration only inspects the route metadata that flask-openapi3 needs to
build the spec, so an in-memory SQLite URI is sufficient. All background tasks
are disabled so that no scheduler/indexer/fetcher work runs during the dump.
"""

from OpenMediaMatch.storage.postgres.impl import DefaultOMMStore
from threatexchange.content_type.photo import PhotoContent
from threatexchange.content_type.video import VideoContent
from threatexchange.exchanges.impl.static_sample import StaticSampleSignalExchangeAPI
from threatexchange.signal_type.md5 import VideoMD5Signal
from threatexchange.signal_type.pdq.signal import PdqSignal

DATABASE_URI = "sqlite:///:memory:"

PRODUCTION = False
UI_ENABLED = True
ROLE_HASHER = True
ROLE_MATCHER = True
ROLE_CURATOR = True

TASK_FETCHER = False
TASK_INDEXER = False
TASK_INDEX_CACHE = False

STORAGE_IFACE_INSTANCE = DefaultOMMStore(
    signal_types=[PdqSignal, VideoMD5Signal],
    content_types=[PhotoContent, VideoContent],
    exchange_types=[StaticSampleSignalExchangeAPI],
)
