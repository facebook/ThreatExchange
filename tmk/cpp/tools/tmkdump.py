#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved

import sys
import struct
import errno

# ================================================================
# This is a sample of how to use Python to read a .tmk file written
# by the C++ code (feat2tmk.cpp, tmkfv.cpp).
# ================================================================

# tmkiotypes.h snippet:
#
# struct FeatureVectorFileHeader {
#   char projectMagic[TMK_MAGIC_LENGTH];
#   char fileTypeMagic[TMK_MAGIC_LENGTH];
#
#   // Not present in the data, but essential information on the provenance
#   // of the data.
#   char frameFeatureAlgorithmMagic[TMK_MAGIC_LENGTH];
#   int framesPerSecond;
#
#   int numPeriods; // a.k.a. P
#   int numFourierCoefficients; // a.k.a m
#
#   int frameFeatureDimension; // a.k.a d
#   int pad; // Make multiple of 16 to ease hex-dump reading
#
# };
#
# See also tmkfv.cpp.


def dump_tmk_file(filename):
    '''
    Reads a .tmk file and prints it. See tmkiotypes.h.
    '''

    expected_project_magic = 'TMK1'
    expected_file_type_magic = 'FVEC'

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

        frames_per_second = handle.read(4)
        num_periods = handle.read(4)
        num_fourier_coefficients = handle.read(4)
        frame_feature_dimension = handle.read(4)
        frame_feature_count = handle.read(4)

        frames_per_second = struct.unpack('i', frames_per_second)[0]
        num_periods = struct.unpack('i', num_periods)[0]
        num_fourier_coefficients = struct.unpack('i',
            num_fourier_coefficients)[0]
        frame_feature_dimension = struct.unpack('i',
            frame_feature_dimension)[0]
        frame_feature_count = struct.unpack('i',
            frame_feature_count)[0]

        print("filename                      %s" % filename)
        print("project_magic                 %s" % project_magic)
        print("file_type_magic               %s" % file_type_magic)
        print("frame_feature_algorithm_magic %s" % frame_feature_algorithm_magic)
        print("frames_per_second             %d" % frames_per_second)
        print("num_periods                   %d" % num_periods)
        print("num_fourier_coefficients      %d" % num_fourier_coefficients)
        print("frame_feature_dimension       %d" % frame_feature_dimension)
        print("frame_feature_count           %d" % frame_feature_count)

        periods = struct.unpack('i' * num_periods, handle.read(4 * num_periods))
        print(periods)

        fourier_coefficients = struct.unpack('f' * num_fourier_coefficients,
            handle.read(4 * num_fourier_coefficients))
        print(fourier_coefficients)

        pure_average_feature = struct.unpack('f' * frame_feature_dimension,
            handle.read(4 * frame_feature_dimension))
        print(pure_average_feature)

        for i in range(0, num_periods):
            for j in range(0, num_fourier_coefficients):
                cos_feature = struct.unpack('f' * frame_feature_dimension,
                    handle.read(4 * frame_feature_dimension))
                print("cos:%d:%d " % (i, j), end='')
                print(cos_feature)
        for i in range(0, num_periods):
            for j in range(0, num_fourier_coefficients):
                sin_feature = struct.unpack('f' * frame_feature_dimension,
                    handle.read(4 * frame_feature_dimension))
                print("sin:%d:%d " % (i, j), end='')
                print(sin_feature)


# ================================================================
try:
    for filename in sys.argv[1:]:
        dump_tmk_file(filename)
except IOError as e:
    if e.errno == errno.EPIPE:
        pass  # e.g. we were piped to head which is harmless
    else:
        raise e
