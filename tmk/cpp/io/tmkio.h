// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

// ================================================================
// Methods for reading/writing TMK file formats: .vstr/.feat/.tmk file
// headers, RGB frame-raster contents, and float-array contents.
// ================================================================

#ifndef TMKIO_H
#define TMKIO_H

#include <tmk/cpp/io/tmkiotypes.h>

#include <stdio.h>
#include <vector>

namespace facebook {
namespace tmk {
namespace io {

// ----------------------------------------------------------------
FILE* openFileOrDie(const char* filename, const char* mode, const char* argv0);

// ----------------------------------------------------------------
TMKFramewiseAlgorithm algoFromMagic(char magic[TMK_MAGIC_LENGTH]);
TMKFramewiseAlgorithm algoFromMagicOrDie(
    char* argv0,
    char magic[TMK_MAGIC_LENGTH],
    char* fromFileName);
void reportUnrecognizedAlgorithmMagic(
    char* argv0,
    char magic[4],
    char* fromFileName);
bool algoToMagic(TMKFramewiseAlgorithm algorithm, char magic[TMK_MAGIC_LENGTH]);
TMKFramewiseAlgorithm algoFromLowercaseName(std::string name);
std::string algorithmToName(TMKFramewiseAlgorithm algorithm);

// ----------------------------------------------------------------
bool readDecodedVideoStreamFileHeader(
    FILE* fp,
    DecodedVideoStreamFileHeader* pheader,
    const char* programName);

bool readFrameFeaturesFileHeader(
    FILE* fp,
    FrameFeaturesFileHeader* pheader,
    TMKFramewiseAlgorithm& algorithm,
    const char* programName);

bool readFeatureVectorFileHeader(
    FILE* fp,
    FeatureVectorFileHeader* pheader,
    TMKFramewiseAlgorithm& algorithm,
    const char* programName);

// ----------------------------------------------------------------
bool writeDecodedVideoStreamFileHeader(
    FILE* fp,
    int frameHeight,
    int frameWidth,
    int framesPerSecond,
    const char* programName);

bool writeFrameFeaturesFileHeader(
    FILE* fp,
    TMKFramewiseAlgorithm algorithm,
    int frameFeatureDimension,
    int framesPerSecond,
    const char* programName);

bool writeFeatureVectorFileHeader(
    FILE* fp,
    TMKFramewiseAlgorithm algorithm, // provenance
    int framesPerSecond, // provenance
    int numPeriods, // a.k.a. P
    int numFourierCoefficients, // a.k.a m
    int frameFeatureDimension, // a.k.a d
    int frameFeatureCount,
    const char* programName);

// ----------------------------------------------------------------
bool checkMagic(char actual[4], char* expected, const char* programName);
char makePrintable(char c);

// ----------------------------------------------------------------
// Precondition: buffer is already allocated.
bool readRGBTriples(
    unsigned char* buffer,
    int height,
    int width,
    FILE* fp,
    bool& eof);

// ----------------------------------------------------------------
// Precondition: vector is already allocated.
bool readFloatVector(std::vector<float>& vector, FILE* fp, bool& eof);

bool writeFloatVector(const std::vector<float>& vector, FILE* fp);

bool readIntVector(std::vector<int>& vector, FILE* fp);

bool writeIntVector(const std::vector<int>& vector, FILE* fp);

} // namespace io
} // namespace tmk
} // namespace facebook

#endif // TMKIO_H
