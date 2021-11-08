# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
import settings


def load_custom_actioner(name: str):
    try:
        from settings import CUSTOM_ACTION_PERFORMERS

        return CUSTOM_ACTION_PERFORMERS.get(name)
    except Exception:
        return None
