#!/usr/bin/env python
# Copyright (c) Meta Platforms, Inc. and affiliates.

from setuptools import setup


extras_require = {
    "cli": [
        "pandas==1.3.5",
        "numpy>=1.23.2",
    ]
}

all_extras = set(sum(extras_require.values(), []))
extras_require["test"] = sorted({"pytest==6.2.1", "freezegun==1.1.0"} | all_extras)
extras_require["package"] = ["wheel"]
extras_require["lint"] = ["black==22.3.0"]
extras_require["type"] = ["types-requests==2.27.1", "types-freezegun==1.1.7"]
extras_require["all"] = sorted(set(sum(extras_require.values(), [])))

setup(
    name="hmalib",
    description="Convenience package for hmalib. Probably don't distribute it.",
    install_requires=[
        "boto3==1.20.37",
        "boto3-stubs[essential,sns,dynamodbstreams]==1.17.14.0",
        "threatexchange[faiss,pdq_hasher]==1.0.10",
        "bottle==0.12.20",
        "apig-wsgi==2.13.0",
        "pyjwt[crypto]==2.4.0",
        "methodtools==0.4.5",
        "requests==2.31.0",
    ],
    extras_require=extras_require,
    entry_points={
        "console_scripts": ["hmacli = hmalib.scripts.cli.main:main"],
    },
)
