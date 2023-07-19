# Copyright (c) Meta Platforms, Inc. and affiliates.

import shutil
from pathlib import Path
import os
import subprocess
import argparse
import sys
import logging

DIR = Path(__file__).resolve().parent
PARENTDIR = Path(__file__).resolve().parents[1]

SETUP = "setup.py"
MANIFEST = "MANIFEST.in"
DIST = "dist"


def get_argparse() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-r",
        "--release",
        help="If release, will package the source distribution in the root dir.",
        action="store_true",
    )
    ap.add_argument(
        "-i",
        "--install",
        help="If install, will install vpdq locally.",
        action="store_true",
    )
    return ap


def main():
    ap = get_argparse()
    args = ap.parse_args()

    logger = logging.getLogger("vpdq-release.py")
    logger.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO)

    # TODO: Why is this done? It makes running setup.py directly impossible.
    # This has to be changed so that it's possible to run setup.py directly.
    shutil.copy(DIR / SETUP, PARENTDIR / SETUP)
    shutil.copy(DIR / MANIFEST, PARENTDIR / MANIFEST)
    if args.release:
        logger.info("Packaging vpdq Python binding source for distribution")
        try:
            sdist_proc = subprocess.run(
                ["python3", "setup.py", "sdist"],
                cwd=PARENTDIR,
                check=True,
                capture_output=True,
            )
            logger.info(str(sdist_proc.stdout, "utf-8"))
        except subprocess.CalledProcessError as e:
            logger.critical(str(e.stderr, "utf-8"))
            logger.critical("Failed to package vpdq for distribution.")
            sys.exit(1)

        if (DIR / DIST).exists() and (DIR / DIST).is_dir():
            shutil.rmtree(DIR / DIST)
        shutil.move(PARENTDIR / DIST, DIR / DIST)
    if args.install:
        logger.info("Installing vpdq Python binding")
        try:
            install_proc = subprocess.run(
                ["pip3", "install", "-e", "."],
                cwd=PARENTDIR,
                check=True,
                capture_output=True,
            )
            logger.info(str(install_proc.stdout, "utf-8"))
        except subprocess.CalledProcessError as e:
            logger.critical(str(e.stderr, "utf-8"))
            logger.critical("Failed to install vpdq library.")
            sys.exit(1)

    os.remove(PARENTDIR / SETUP)
    os.remove(PARENTDIR / MANIFEST)


if __name__ == "__main__":
    main()
