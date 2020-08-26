#!/usr/bin/env python2
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

# You may need
#   sudo pip install pillow
# or
#   sudo pip2 install pillow
# to get PIL (Python image library)
from PIL import Image

import sys
import os
import errno

# ================================================================
# This is a sample of how to use Python to read a raw RGB-frame-raster file
# written by ffmpeg.exe. See also ./README.md.
# ================================================================


def dump_vstr(filename, frame_height, frame_width):
    '''
    Reads a raw RGB-frame-rasters file and prints it.
    '''

    with open(filename, 'rb') as handle:

        prefix = os.path.basename(filename).replace('.rgb', '')
        fno = 0
        while True:
            frame = handle.read(3 * frame_height * frame_width)
            if not frame:
                break
            image = Image.frombytes('RGB', (frame_width, frame_height), frame)
            fname = "%s-%08d.jpg" % (prefix, fno)
            image.save(fname, format='jpeg')
            print(fname)
            fno += 1


# ================================================================
height = 256
width = 256
try:
    for filename in sys.argv[1:]:
        dump_vstr(filename, height, width)
except IOError as e:
    if e.errno == errno.EPIPE:
        pass  # e.g. we were piped to head which is harmless
    else:
        raise e
