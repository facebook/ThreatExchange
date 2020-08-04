#!/usr/bin/env python
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import sys

from setuptools import setup, find_packages
from codecs import open
from os import path


here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
    description = f.read()

setup(
    name='pytx3',
    version='0.0.1',
    description='Python Library for Facebook ThreatExchange',
    long_description=long_description,
    author='Facebook',
    author_email='threatexchange@fb.com',
    license='BSD',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='facebook threatexchange',
    url='https://www.github.com/facebook/ThreatExchange',
    packages=find_packages(exclude=['tests']),
    install_requires=[],
    scripts=[],
)
