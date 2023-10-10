# Copyright (c) Meta Platforms, Inc. and affiliates.

"""
Why do all the flask authors love module state so much?

Tasks need to refer to their scheduler instance, but only
json-serializable data can be passed as args. So provide
this as a way to get a static instance.
"""

from flask_apscheduler import APScheduler

_SCHEDULER = None


def get_apscheduler() -> APScheduler:
    global _SCHEDULER
    if _SCHEDULER is None:
        _SCHEDULER = APScheduler()
    return _SCHEDULER
