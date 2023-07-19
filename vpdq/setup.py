# Copyright (c) Meta Platforms, Inc. and affiliates.

from setuptools import setup
from setuptools.extension import Extension
from setuptools.command.build_ext import build_ext
import sys
import subprocess
from pathlib import Path
import os
import logging

logger = logging.getLogger("setup.py")
logger.setLevel(logging.INFO)
logging.basicConfig()

# setup.py cannot be run directly, it has to be run through vpdq-release.py
# because the paths are relative to the parent to the vpdq directory.
# THIS HAS TO BE CHANGED!

DIR = Path(__file__).parent
read_me = DIR / Path("vpdq/python/README.md")
long_description = read_me.read_text()
version = (DIR / "vpdq/version.txt").read_text(encoding="utf-8").strip()
cpp_dir = DIR / "vpdq/cpp"
build_dir = cpp_dir / "build"

# Get the library directories and include directories from the environment variables
# These variables should be set in the CMakeLists.txt file
lib_dirs = os.getenv("LIBRARY_DIRS", "").split(":")
include_dirs = os.getenv("INCLUDE_DIRS", "").split(":")
# Something about this doesn't work on Windows,
# but it could be the environment variable passing itself.
include_dirs.extend(["vpdq/pdq", "./"])


class build_ext(build_ext):
    def run(self):
        try:
            # TODO: Clean the build directory AND vpdq.cpp before building
            # Otherwise it won't generate a new version of vpdq.cpp for each run
            logger.info("Creating build directory...")
            subprocess.run(["mkdir", "build"], cwd=cpp_dir, check=False)
            logger.info("Running CMake...")
            cmake_proc = subprocess.run(
                ["cmake", ".."], cwd=build_dir, check=True, capture_output=True
            )
            logger.info(str(cmake_proc.stdout, "utf-8"))
            logger.info("Compiling with Make...")
            make_proc = subprocess.run(
                ["make"], cwd=build_dir, check=True, capture_output=True
            )
            logger.info(str(make_proc.stdout, "utf-8"))
        except subprocess.CalledProcessError as e:
            logger.critical(str(e.stderr, "utf-8"))
            logger.critical("Failed to compile vpdq library.")
            sys.exit(1)
        super().run()


EXTENSIONS = [
    Extension(
        "vpdq",
        sources=["vpdq/python/vpdq.pyx"],
        language="c++",
        libraries=[
            "avdevice",
            "avfilter",
            "avformat",
            "avcodec",
            "swresample",
            "swscale",
            "avutil",
        ],
        extra_objects=["vpdq/cpp/build/libvpdqlib.a"],
        library_dirs=lib_dirs,
        include_dirs=include_dirs,
        extra_compile_args=["--std=c++14"],
    )
]

setup(
    name="vpdq",
    author="Facebook",
    description="Python bindings for Facebook VPDQ hash",
    author_email="threatexchange@fb.com",
    version=version,
    license_files="LICENSE.txt",
    license="BSD",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=["cython"],
    include_package_data=True,
    cmdclass={"build_ext": build_ext},
    ext_modules=EXTENSIONS,
    entry_points={"console_scripts": ["vpdq = vpdq:_cli"]},
)
