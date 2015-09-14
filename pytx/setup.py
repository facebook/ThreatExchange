#!/usr/bin/env python

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
    description = f.read()

setup(
    name='pytx',
    version='0.2.0',
    description='Python Library for Facebook ThreatExchange',
    long_description=long_description,
    author='Mike Goffin',
    author_email='mgoffin@gmail.com',
    license='BSD',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='facebook threatexchange',
    url='https://www.github.com/facebook/ThreatExchange',
    packages=find_packages(exclude=['docs', 'tests']),
    install_requires=['requests[security]==2.7.0'],
    scripts=['scripts/get_compromised_credentials.py',
             'scripts/get_indicators.py',
             'scripts/get_members.py',
             'scripts/malware_api.py',
             'scripts/malware_grabber.py'],
)
