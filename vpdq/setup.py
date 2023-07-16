# Copyright (c) Meta Platforms, Inc. and affiliates.

from setuptools import setup
from setuptools.extension import Extension
from setuptools.command.build_ext import build_ext
import sys
import subprocess
from pathlib import Path
import os
import logging

DIR = Path(__file__).parent
read_me = DIR / Path("vpdq/python/README.md")
long_description = read_me.read_text()
version = (DIR / "vpdq/version.txt").read_text(encoding="utf-8").strip()

# Get the library directories and include directories from the environment variables
# These variables should be set in the CMakeLists.txt file
lib_dirs = os.getenv("LIBRARY_DIRS", "").split(":")
include_dirs = os.getenv("INCLUDE_DIRS", "").split(":")
include_dirs.extend(["../../../pdq/cpp/common/", "."])  # Can this be changed?


class build_ext(build_ext):
    def run(self):
        try:
            logging.info("Creating build directory...")
            subprocess.call(["mkdir", "build"], cwd=DIR / "vpdq/cpp")
            logging.info("Running CMake...")
            subprocess.check_call(["cmake", ".."], cwd=DIR / "vpdq/cpp/build")
            logging.info("Compiling with Make...")
            subprocess.check_call(["make"], cwd=DIR / "vpdq/cpp/build")
        except subprocess.CalledProcessError as e:
            logging.error(e.output)
            logging.error("Failed to clean or compile")
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
