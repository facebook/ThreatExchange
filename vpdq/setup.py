# Copyright (c) Meta Platforms, Inc. and affiliates.

from setuptools import setup
from setuptools.extension import Extension
from setuptools.command.build_ext import build_ext
import sys
import subprocess
from pathlib import Path
import logging
import shutil
from typing import List

logger = logging.getLogger("setup.py")
logger.setLevel(logging.INFO)
logging.basicConfig()

DIR = Path(__file__).parent

CPP_DIR = DIR / "cpp"
CPP_BUILD_DIR = CPP_DIR / "build"
CYTHON_CPP_PATH = DIR / "python/vpdq.cpp"
CYTHON_PYX_PATH = DIR / "python/vpdq.pyx"
LIBVPDQ_PATH = CPP_BUILD_DIR / "libvpdq.a"
LIBRARIES_DIRS_PATH = CPP_DIR / "libraries-dirs.txt"

lib_dirs: List[str] = []
include_dirs: List[str] = [str(CPP_DIR)]
libav_libraries: List[str]= [
    "avdevice",
    "avfilter",
    "avformat",
    "avcodec",
    "swresample",
    "swscale",
    "avutil",
]
libraries: List[str] = libav_libraries


def make_clean() -> None:
    """Remove CMake and Cython build files from previous runs."""
    logger.info(f"Removing CPP build directory {CPP_BUILD_DIR}...")
    if Path.exists(CPP_BUILD_DIR):
        shutil.rmtree(CPP_BUILD_DIR)

    logger.info(f"Removing compiled Cython files {CYTHON_CPP_PATH}...")
    Path.unlink(CYTHON_CPP_PATH, missing_ok=True)

    logger.info(f"Removing libraries-dir.txt file {LIBRARIES_DIRS_PATH}...")
    Path.unlink(LIBRARIES_DIRS_PATH, missing_ok=True)


class build_ext(build_ext):
    def run(self):
        global lib_dirs
        try:
            make_clean()
            logger.info("Creating CPP build directory...")
            Path.mkdir(CPP_BUILD_DIR, exist_ok=True)

            logger.info("Running CMake...")
            cmake_proc = subprocess.run(
                ["cmake", f"{CPP_DIR}"],
                cwd=CPP_BUILD_DIR,
                check=True,
                capture_output=True,
            )
            logger.info(str(cmake_proc.stdout, "utf-8"))

            logger.info("Compiling libvpdq with Make...")
            make_proc = subprocess.run(
                ["make"], cwd=CPP_BUILD_DIR, check=True, capture_output=True
            )
            logger.info(str(make_proc.stdout, "utf-8"))

            # Add the directories of required libraries that are found from CMake to lib_dirs
            with open(LIBRARIES_DIRS_PATH, "r") as file:
                lib_dirs = [line.strip() for line in file]

        except subprocess.CalledProcessError as e:
            logger.critical(str(e.stderr, "utf-8"))
            logger.critical("Failed to compile vpdq library.")
            sys.exit(1)
        super().run()


EXTENSIONS = [
    Extension(
        name="vpdq",
        sources=[str(CYTHON_PYX_PATH)],
        language="c++",
        libraries=libraries,
        extra_objects=[str(LIBVPDQ_PATH)],
        library_dirs=lib_dirs,
        include_dirs=include_dirs,
    )
]


def get_version():
    version = (DIR / "version.txt").read_text(encoding="utf-8").strip()
    return version


setup(
    version=get_version(),
    cmdclass={"build_ext": build_ext},
    ext_modules=EXTENSIONS,
    entry_points={"console_scripts": ["vpdq = vpdq:_cli"]},
)
