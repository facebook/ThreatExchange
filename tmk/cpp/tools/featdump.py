#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import sys
import struct
import errno

# ================================================================
# This is a sample of how to use Python to read a .feat file written
# by the C++ code (vstr2feat.cpp, tmkfv.cpp).
# ================================================================

# tmkiotypes.h snippet:
#
# struct FrameFeaturesFileHeader {
#   char projectMagic[TMK_MAGIC_LENGTH];
#   char fileTypeMagic[TMK_MAGIC_LENGTH];
#
#   char frameFeatureAlgorithmMagic[TMK_MAGIC_LENGTH];
#   int frameFeatureDimension;
#
#   int framesPerSecond;
#   int pad[3]; // Make multiple of 16 to ease hex-dump reading
#
#   // Frame-count is left unspecified here so that executables can stream data
#   // to one another on a pipe if desired
# };

def dump_feat(filename):
    '''
    Reads a .feat file and prints it. See tmkiotypes.h.
    '''

    expected_project_magic = 'TMK1'
    expected_file_type_magic = 'FEAT'

    with open(filename, 'rb') as handle:
        project_magic = handle.read(4).decode('ascii')
        file_type_magic = handle.read(4).decode('ascii')
        frame_feature_algorithm_magic = handle.read(4).decode('ascii')

        if project_magic != expected_project_magic:
            msg = "File \"%s\" has project magic \"%s\" not \"%s\"." % \
                (filename, project_magic, expected_project_magic)
            raise Exception(msg)
        if file_type_magic != expected_file_type_magic:
            msg = "File \"%s\" has file-type magic \"%s\" not \"%s\"." % \
                (filename, file_type_magic, expected_file_type_magic)
            raise Exception(msg)

        frame_feature_dimension = handle.read(4)
        frames_per_second = handle.read(4)
        handle.read(4)  # seek past
        handle.read(4)  # seek past
        handle.read(4)  # seek past

        frame_feature_dimension = struct.unpack('i', frame_feature_dimension)[0]
        frames_per_second = struct.unpack('i', frames_per_second)[0]

        print("filename                      %s" % filename)
        print("project_magic                 %s" % project_magic)
        print("file_type_magic               %s" % file_type_magic)
        print("frame_feature_algorithm_magic %s" % frame_feature_algorithm_magic)
        print("frame_feature_dimension       %d" % frame_feature_dimension)
        print("frames_per_second             %d" % frames_per_second)

        frame_features = []
        while True:
            frame_feature = handle.read(4 * frame_feature_dimension)
            if not frame_feature:
                break
            frame_feature = struct.unpack('f' * frame_feature_dimension,
                frame_feature)
            frame_features.append(frame_feature)
        for frame_feature in frame_features:
            print(frame_feature)


# ================================================================
try:
    for filename in sys.argv[1:]:
        dump_feat(filename)
except IOError as e:
    if e.errno == errno.EPIPE:
        pass  # e.g. we were piped to head which is harmless
    else:
        raise e
