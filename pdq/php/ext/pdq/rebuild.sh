#!/bin/bash
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

set -e

make clean
phpize
./configure --enable-pdq
make
echo
echo REBUILT
