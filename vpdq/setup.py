from setuptools import setup
from setuptools.extension import Extension
from setuptools.command.build_py import build_py
import sys
import subprocess
import os
import numpy
from pathlib import Path

read_me = Path.cwd() / Path("README.md")
long_description = read_me.read_text()


class Build(build_py):
    """Customized setuptools build command - builds protos on build."""

    def run(self):
        os.chdir("cpp")
        command = ["mkdir", "build"]
        subprocess.call(command)
        os.chdir("build")
        command = ["cmake", ".."]
        if subprocess.call(command) != 0:
            sys.exit(-1)
        command = ["make"]
        if subprocess.call(command) != 0:
            sys.exit(-1)
        os.chdir("../../")
        build_py.run(self)


EXTENSIONS = [
    Extension(
        "vpdq",
        ["python/vpdq.pyx"],
        extra_objects=["cpp/build/libvpdqlib.a"],
        include_dirs=["../", numpy.get_include()],
        language="c++",
        extra_compile_args=["--std=c++11"],
    )
]

setup(
    name="vpdq",
    author="Facebook",
    descripition="Python bindings for Facebook VPDQ hash",
    author_email="threatexchange@fb.com",
    version="0.1.0",
    license_files="LICENSE.txt",
    license="BSD",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        "numpy",
        "cython",
        "opencv-python",
    ],
    include_package_data=True,
    cmdclass={"build_py": Build},
    ext_modules=EXTENSIONS,
)
