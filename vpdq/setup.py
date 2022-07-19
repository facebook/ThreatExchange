from setuptools import setup
from setuptools.extension import Extension
from setuptools.command.build_ext import build_ext                                     
import sys
import subprocess
import os
import numpy
from pathlib import Path

read_me = Path.cwd() / Path("vpdq/README.md")
long_description = read_me.read_text()

class build_ext(build_ext):
    def run(self):
        os.chdir("vpdq/cpp")
        command = ["make"]
        if subprocess.call(command) != 0:
            sys.exit(-1)
        os.chdir("../../")
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
    descripition="Python bindings for Facebook VPDQ hash",
    author_email="threatexchange@fb.com",
    version="0.1.7",
    license_files="LICENSE.txt",
    license="BSD",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        "numpy",
        "cython",
        "opencv-python"
    ],
    include_package_data=True,
    cmdclass={'build_ext': build_ext},
    ext_modules=EXTENSIONS,
)
