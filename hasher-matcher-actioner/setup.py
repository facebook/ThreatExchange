#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

from setuptools import setup


extras_require = {
    "cli": [
        "pandas",
        "numpy",
    ]
}

all_extras = set(sum(extras_require.values(), []))
extras_require["test"] = sorted({"pytest"} | all_extras)
extras_require["package"] = ["wheel"]
extras_require["lint"] = ["black"]
extras_require["all"] = sorted(set(sum(extras_require.values(), [])))

setup(
    name="hmalib",
    description="Convenience package for hmalib. Probably don't distribute it.",
    install_requires=[
        "boto3",
        "boto3-stubs[essential,sns]==1.17.14.0",
        "threatexchange[faiss,pdq_hasher]>=0.0.23",
        "bottle",
        "apig_wsgi",
        "pyjwt[crypto]==2.1.0",
        "requests==2.25.1",
    ],
    extras_require=extras_require,
    entry_points={"console_scripts": ["hmacli = hmalib.scripts.cli.main:main"]},
)
