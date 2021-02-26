# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

class HmaLiteConfig:
    DEBUG = False
    TESTING = False

    INDEX_FILE = "~/.hmalite/index.te"


class HmaLiteProdConfig(HmaLiteConfig):
    pass


class HmaLiteDevConfig(HmaLiteConfig):
    DEBUG = True
