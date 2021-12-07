#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import sys
from codecs import open
from os import path

from setuptools import find_packages, setup


here = path.abspath(path.dirname(__file__))
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

with open(path.join(here, "DESCRIPTION.rst"), encoding="utf-8") as f:
    description = f.read()

with open(path.join(here, "version.txt"), encoding="utf-8") as f:
    version = f.read().strip()

extras_require = {
    "faiss": ["faiss-cpu>=1.6.3", "numpy"],
    "pdq_hasher": [
        "numpy",
        "pdqhash>=0.2.2",
        "Pillow",
    ],
    "ocr": [
        "pytesseract",
    ],
    "pdf": [
        "py-tlsh",
        "pdfminer.six",
    ],
}

all_extras = set(sum(extras_require.values(), []))
extras_require["test"] = sorted({"pytest"} | all_extras)
extras_require["package"] = ["wheel"]
extras_require["lint"] = ["black"]
extras_require["types"] = ["mypy", "types-python-dateutil", "types-requests"]
extras_require["all"] = sorted(set(sum(extras_require.values(), [])))

setup(
    name="threatexchange",
    version=version,
    description="Python Library for Facebook ThreatExchange",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Facebook",
    author_email="threatexchange@fb.com",
    license="BSD",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.6",
    ],
    keywords="facebook threatexchange",
    url="https://www.github.com/facebook/ThreatExchange",
    packages=find_packages(exclude=["tests*"]),
    install_requires=[
        "python-Levenshtein",
        "requests>=2.26.0",
        "urllib3>=1.26.0",  # For allow_methods
        "dataclasses",
        "python-dateutil",
    ],
    extras_require=extras_require,
    entry_points={"console_scripts": ["threatexchange = threatexchange.cli.main:main"]},
)
