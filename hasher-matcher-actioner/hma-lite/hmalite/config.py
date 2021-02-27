# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import os.path


class HmaLiteConfig:
    DEBUG = False
    TESTING = False

    INDEX_FILE = os.path.expanduser("~/.hmalite/index.te")
    UPLOADS_FOLDER = os.path.expanduser("~/.hmalite/uploads")


class HmaLiteProdConfig(HmaLiteConfig):
    pass


class HmaLiteDevConfig(HmaLiteConfig):
    DEBUG = True
