# Copyright (c) Meta Platforms, Inc. and affiliates.

import logging


def get_logger(name=__name__, level=logging.INFO):
    """
    This pattern prevents creates implicitly creating a root logger by creating the sub-logger named __name__
    Also by default sets level to INFO
    """

    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger
