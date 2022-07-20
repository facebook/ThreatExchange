from setuptools import setup
from setuptools.extension import Extension
from setuptools.command.build_ext import build_ext                                     
import sys
import subprocess
import os
import numpy
from pathlib import Path

DIR = Path(__file__).parent
read_me = DIR / Path("vpdq/README.md")
long_description = read_me.read_text()
version = (DIR / "vpdq/version.txt").read_text(encoding="utf-8").strip()

class build_ext(build_ext):
    def run(self):
        command = ["make"]
        try:
            subprocess.check_call(command, cwd="vpdq/cpp")
        except subprocess.CalledProcessError as e:
            print(e.output)
            print("fail to compile vpdq/pdq library")
            sys.exit(1)
        super().run()

EXTENSIONS = [
    Extension(
        "vpdq",
        ["vpdq/python/vpdq.pyx"],
        extra_objects=["vpdq/cpp/libvpdq.a"],
        include_dirs=[".", numpy.get_include()],
        language="c++",
        extra_compile_args=["--std=c++11"],
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
    install_requires=[
        "numpy",
        "cython",
        "opencv-python",
        "opencv-python-headless"
    ],
    include_package_data=True,
    cmdclass={'build_ext': build_ext},
    ext_modules=EXTENSIONS,
)
