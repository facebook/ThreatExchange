# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import sys
import functools

if sys.version_info >= (3, 8):
    from importlib import metadata as importlib_metadata
else:
    import importlib_metadata


@functools.lru_cache(maxsize=None)
def importlib_metadata_get(group: str):
    ep = importlib_metadata.entry_points()
    if hasattr(ep, "select"):
        return ep.select(group=group)  # type: ignore # method checked manually.
    else:
        return ep.get(group, ())


# 5 is arbitrary (seems unlikely >5 custom impl used together)
@functools.lru_cache(maxsize=5)
def load_extension_impl(entry_point_name: str):
    """
    Attempts to load an entry point from the `hmalib_extensions`
    group specifed in setup.py
    TODO more typing and validation should be done here. for now:
    ONLY USE THIS OR MAKE CHANGES IF YOU KNOW WHAT YOU ARE DOING. :)
    """
    for ep in importlib_metadata_get(group="hmalib_extensions"):
        if ep.name == entry_point_name:
            return ep.load()
    return None
