#!/bin/sh
# Copyright (c) Meta Platforms, Inc. and affiliates.

for mp4 in ../sample-videos/*.mp4; do
  tmk=$(echo $(basename $mp4) | sed 's/mp4/tmk/')
  ../cpp/tmk-hash-video -i $mp4 -o $tmk -f /usr/local/bin/ffmpeg
done
