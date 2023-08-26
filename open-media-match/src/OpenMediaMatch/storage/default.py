# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
The default store for accessing persistent data on OMM.
"""

from OpenMediaMatch.storage import interface
from OpenMediaMatch.storage import mocked

class DefaultOMMStore(mocked.MockedUnifiedStore, interface.IUnifiedStore):
    """
    The default store for accessing persistent data on OMM.

    During the initial development, the storage is mostly mocked, but
    that will go away as implementation progresses.

    In implementation, don't refer to DefaultOMMStore directly, but
    instead to the interfaces to allow future authors more ease in
    extending. 

    Data is stored in a combination of:
      * Static config set by deployment (e.g. installed SignalTypes)
      * PostGres-backed tables (e.g. info downloaded from external APIs)
      * Blobstore (e.g. built indices) 
    """
