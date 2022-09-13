# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

from pathlib import Path
from os import path
from setuptools import find_packages, setup

here = Path(__file__).parent

description = (here / "DESCRIPTION.rst").read_text(encoding="utf-8").strip()
long_description = (here / "README.md").read_text(encoding="utf-8").strip()
version = (here / "version.txt").read_text(encoding="utf-8").strip()

extensions_dir = here / "threatexchange" / "extensions"

extras_require = {}

for extension_dir in extensions_dir.iterdir():
    requirements = extension_dir / "requirements.txt"
    if requirements.is_file():
        extras_require[f"extensions.{extension_dir.name}"] = (
            requirements.read_text().strip().split("\n")
        )

all_extras = set(sum(extras_require.values(), []))
extras_require["test"] = sorted({"pytest"} | all_extras)
extras_require["package"] = ["wheel"]
extras_require["lint"] = ["black"]
extras_require["types"] = ["mypy", "types-python-dateutil", "types-requests"]
extras_require["all"] = sorted(set(sum(extras_require.values(), [])))

setup(
    name="threatexchange",
    version=version,
    description="Python Library for Signal Exchange",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Facebook",
    author_email="threatexchange@fb.com",
    license="BSD",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.8",
    ],
    keywords="facebook threatexchange ncmec stopncii pdq",
    url="https://www.github.com/facebook/ThreatExchange",
    packages=find_packages(exclude=["tests*"]),
    install_requires=[
        "python-Levenshtein",
        "requests>=2.26.0",
        "urllib3>=1.26.0",  # For allow_methods
        "python-dateutil",
        "dacite",
        "Pillow",  # pdq
        "pdqhash>=0.2.2",  # pdq
        "faiss-cpu>=1.6.3",  # faiss
        "numpy>=1.23.2",  # faiss
    ],
    extras_require=extras_require,
    entry_points={"console_scripts": ["threatexchange = threatexchange.cli.main:main"]},
)
