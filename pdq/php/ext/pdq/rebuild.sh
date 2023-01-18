#!/bin/bash
# Copyright (c) Meta Platforms, Inc. and affiliates.

set -e

make clean
phpize
./configure --enable-pdq
make
echo
echo REBUILT
