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
import struct
import errno

# ================================================================
# This is a sample of how to use Python to read a .vstr file written
# by the C++ code (vid2vstr.cpp).
# ================================================================

# tmkiotypes.h snippet:
#
# struct DecodedVideoStreamFileHeader {
#   char projectMagic[TMK_MAGIC_LENGTH];
#   char fileTypeMagic[TMK_MAGIC_LENGTH];
#
#   int frameHeight;
#   int frameWidth;
#
#   int framesPerSecond;
#
#   int pad[3]; // Make multiple of 16 to ease hex-dump reading
#
#   // Frame-count is left unspecified here so that executables can stream data
#   // to one another on a pipe if desired
# };


def dump_vstr(filename):
    '''
    Reads a .vstr file and prints it. See tmkiotypes.h.
    '''

    expected_project_magic = 'TMK1'
    expected_file_type_magic = 'VSTR'

    with open(filename, 'rb') as handle:
        project_magic = handle.read(4).decode('ascii')
        file_type_magic = handle.read(4).decode('ascii')

        if project_magic != expected_project_magic:
            msg = "File \"%s\" has project magic \"%s\" not \"%s\"." % \
                (filename, project_magic, expected_project_magic)
            raise Exception(msg)
        if file_type_magic != expected_file_type_magic:
            msg = "File \"%s\" has file-type magic \"%s\" not \"%s\"." % \
                (filename, file_type_magic, expected_file_type_magic)
            raise Exception(msg)

        frame_height = handle.read(4)
        frame_width = handle.read(4)
        frames_per_second = handle.read(4)
        handle.read(4)  # seek past
        handle.read(4)  # seek past
        handle.read(4)  # seek past

        frame_height = struct.unpack('i', frame_height)[0]
        frame_width = struct.unpack('i', frame_width)[0]
        frames_per_second = struct.unpack('i', frames_per_second)[0]

        print("filename                      %s" % filename)
        print("project_magic                 %s" % project_magic)
        print("file_type_magic               %s" % file_type_magic)
        print("frame_height                  %d" % frame_height)
        print("frame_width                   %d" % frame_width)
        print("frames_per_second             %d" % frames_per_second)

        prefix = os.path.basename(filename).replace('.vstr', '')
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
try:
    for filename in sys.argv[1:]:
        dump_vstr(filename)
except IOError as e:
    if e.errno == errno.EPIPE:
        pass  # e.g. we were piped to head which is harmless
    else:
        raise e
