from setuptools import setup
from setuptools.extension import Extension
from setuptools.command.build_py import build_py
import sys
import subprocess
import os
import numpy


class Build(build_py):
    """Customized setuptools build command - builds protos on build."""
    def run(self):
        os.chdir("cpp")
        command = ["mkdir","build"]
        subprocess.call(command)
        os.chdir("build")
        command = ["cmake",".."]
        if subprocess.call(command) != 0:
            sys.exit(-1)
        command = ["make"]
        if subprocess.call(command) != 0:
            sys.exit(-1)
        os.chdir("../../")
        build_py.run(self)

EXTENSIONS = [
    Extension(
        'python.vpdq',
        ['python/vpdq.pyx'],
        extra_objects=["cpp/build/libvpdqlib.a"],
        include_dirs=['../', numpy.get_include()],
        language='c++',
        extra_compile_args=['--std=c++11'])
]

setup(
    cmdclass={'build_py': Build},
    ext_modules=EXTENSIONS
    )
