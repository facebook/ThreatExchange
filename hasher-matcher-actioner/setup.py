#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

from setuptools import setup


setup(
    name="hmalib",
    description="Convenience package for hmalib. Probably don't distribute it.",
    install_requires=[
        "boto3",
        "boto3-stubs[essential,sns]==1.17.14.0",
        "threatexchange[faiss,pdq_hasher]>=0.0.20",
        "bottle",
        "apig_wsgi",
    ],
)
