// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

// ================================================================
// Data structures for TMK file formats.
// ================================================================

#ifndef TMKIOTYPES_H
#define TMKIOTYPES_H
#include <string>
#include <vector>

namespace facebook {
namespace tmk {
namespace io {

// ----------------------------------------------------------------
// Magic numbers
//
// VSTR: decoded video stream
// VFFF: video frame-features file (input to TMK)
// VFVF: videe feature-vector file (output from TMK)

#define TMK_MAGIC_LENGTH 4

// TMK, productionalized, v1
#define TMK_PROJECT_MAGIC "TMK1"

// Video-stream file format: output of ffmpeg, etc. which writes image
// dimensions and raw RGB byte-triples
#define VSTR_FILETYPE_MAGIC "VSTR"

// Video frame-features file: numerical framewise hashes. Proportional to video
// length.
#define FEAT_FILETYPE_MAGIC "FEAT"

// Video feature-vector file: TMK output. Not proportional to video length.
#define FVEC_FILETYPE_MAGIC "FVEC"

#define PDQ_FLOAT_ALGO_MAGIC "PDQF"

enum class TMKFramewiseAlgorithm {
  UNRECOGNIZED = 0,
  UNIT_TEST = 1,
  PDQ_FLOAT = 3,
};

#define TMK_DEFAULT_FRAMES_PER_SECOND 15

// ----------------------------------------------------------------
struct DecodedVideoStreamFileHeader {
  char projectMagic[TMK_MAGIC_LENGTH];
  char fileTypeMagic[TMK_MAGIC_LENGTH];

  int frameHeight;
  int frameWidth;

  int framesPerSecond;

  int pad[3]; // Make multiple of 16 to ease hex-dump reading

  // Frame-count is left unspecified here so that executables can stream data
  // to one another on a pipe if desired
};

// ----------------------------------------------------------------
struct FrameFeaturesFileHeader {
  char projectMagic[TMK_MAGIC_LENGTH];
  char fileTypeMagic[TMK_MAGIC_LENGTH];

  char frameFeatureAlgorithmMagic[TMK_MAGIC_LENGTH];
  int frameFeatureDimension;

  int framesPerSecond;
  int pad[3]; // Make multiple of 16 to ease hex-dump reading

  // Frame-count is left unspecified here so that executables can stream data
  // to one another on a pipe if desired
};

// ----------------------------------------------------------------
struct FeatureVectorFileHeader {
  char projectMagic[TMK_MAGIC_LENGTH];
  char fileTypeMagic[TMK_MAGIC_LENGTH];

  // Not present in the data, but essential information on the provenance
  // of the data.
  char frameFeatureAlgorithmMagic[TMK_MAGIC_LENGTH];
  int framesPerSecond;

  int numPeriods; // a.k.a. P
  int numFourierCoefficients; // a.k.a m

  int frameFeatureDimension; // a.k.a d
  int frameFeatureCount; // informational: frame-count (time-resampled)
                         // ...in the hashed video
};

} // namespace io
} // namespace tmk
} // namespace facebook

#endif // TMKIOTYPES_H
