#!/bin/bash

set -e

make clean
phpize
./configure --enable-pdq
make
echo
echo REBUILT
