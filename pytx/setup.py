#!/usr/bin/env python

import sys

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
    description = f.read()

install_requires = ['python-dateutil', 'flask']

# For Python < 2.7.9, requests[security] is needed which installs extra packages
# for more secure connections. Python >= 2.7.9 doesn't need this.
if (sys.version_info[0] == 3 or
    (sys.version_info[0] == 2 and
     sys.version_info[1] == 7 and
     sys.version_info[2] >= 9)):
    install_requires.append('requests')
else:
    install_requires.append('requests[security]')

setup(
    name='pytx',
    version='0.5.9',
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
    install_requires=install_requires,
    scripts=['scripts/get_data.py',
             'scripts/post_data.py'],
)
