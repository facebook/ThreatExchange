# Copyright (c) Meta Platforms, Inc. and affiliates.

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
# We might not get any value from splitting these all out
extras_require["test"] = sorted({"pytest"} | all_extras)
extras_require["package"] = ["wheel==0.38.4"]
extras_require["lint"] = ["black"]
extras_require["types"] = [
    "mypy==1.7.1",
    "types-python-dateutil",
    "types-requests",
]
extras_require["all"] = sorted(set(sum(extras_require.values(), [])))
# If you are developing pytx, use this install
# Note that without ffmpeg (for vpdq) you may get errors still
extras_require["dev"] = extras_require["all"]

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
        "requests",
        "urllib3",  # For allow_methods
        "python-dateutil",
        "dacite",
        "Pillow",  # pdq
        "pdqhash",  # pdq
        "faiss-cpu",  # faiss
        "numpy",  # faiss
    ],
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "threatexchange = threatexchange.cli.main:main",
            "tx = threatexchange.cli.main:main",
        ],
    },
    package_data={"threatexchange": ["py.typed"]},
)
