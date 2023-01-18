# Copyright (c) Meta Platforms, Inc. and affiliates.

import shutil
from pathlib import Path
import os
import subprocess
import argparse


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
        help="If release, will return the source distribution in the root dir.",
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
    shutil.copy(DIR / SETUP, PARENTDIR / SETUP)
    shutil.copy(DIR / MANIFEST, PARENTDIR / MANIFEST)
    if args.release:
        print("build vpdq source distribution")
        run_command(["python3", "setup.py", "sdist"], PARENTDIR)
        if (DIR / DIST).exists() and (DIR / DIST).is_dir():
            shutil.rmtree(DIR / DIST)
        shutil.move(PARENTDIR / DIST, DIR / DIST)
    if args.install:
        print("install vpdq source locally")
        run_command(["pip3", "install", "-e", "."], PARENTDIR)
    os.remove(PARENTDIR / SETUP)
    os.remove(PARENTDIR / MANIFEST)


def run_command(command, cwd="."):
    try:
        subprocess.check_call(command, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(e.output)


if __name__ == "__main__":
    main()
