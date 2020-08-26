#!/bin/sh
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

for mp4 in ../sample-videos/*.mp4; do
  tmk=$(echo $(basename $mp4) | sed 's/mp4/tmk/')
  ../cpp/tmk-hash-video -i $mp4 -o $tmk -f /usr/local/bin/ffmpeg
done
