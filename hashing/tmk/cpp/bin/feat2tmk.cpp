// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

// ================================================================
// Step 3 of TMK 3-stage hashing pipeline:
// * vid2vstr (or ffmpeg.exe): .mp4 file to .vstr decoded stream
// * vstr2feat: .vstr file to .feat list of frame-featue vectors
// * feat2tmk: .feat file to .tmk list of TMK cosine/sine features
// ================================================================

#include <tmk/cpp/algo/tmkfv.h>
#include <tmk/cpp/io/tmkio.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

using namespace facebook::tmk;
using namespace facebook::tmk::algo;

// ================================================================
void usage(char* argv0, int exit_rc) {
  FILE* fp = (exit_rc == 0) ? stdout : stderr;
  fprintf(fp, "Usage: %s [options] [input file name]\n", argv0);
  fprintf(fp, "Options:\n");
  fprintf(fp, "--output-feature-vectors-file-name {x}\n");
  fprintf(fp, "-v|--verbose\n");
  exit(exit_rc);
}

// ================================================================
int main(int argc, char** argv) {
  char* outputFeatureVectorsFileName = nullptr;
  bool verbose = false;

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Parse command line
  int argi = 1;
  while ((argi < argc) && argv[argi][0] == '-') {
    char* flag = argv[argi++];
    if (!strcmp(flag, "-h") || !strcmp(flag, "--help")) {
      usage(argv[0], 0);
    } else if (!strcmp(flag, "-v") || !strcmp(flag, "--verbose")) {
      verbose = true;

    } else if (!strcmp(flag, "--output-feature-vectors-file-name")) {
      if ((argc - argi) < 1) {
        usage(argv[0], 1);
      }
      outputFeatureVectorsFileName = argv[argi++];

    } else {
      usage(argv[0], 1);
    }
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Acquire input stream
  FILE* inputFp = stdin;
  char* inputFrameFeaturesFileName = (char*)"(stdin)";
  if ((argc - argi) == 0) {
    // keep stdin
  } else if ((argc - argi) == 1) {
    inputFrameFeaturesFileName = argv[argi];
    inputFp = facebook::tmk::io::openFileOrDie(
        inputFrameFeaturesFileName, (char*)"rb", argv[0]);
  } else {
    usage(argv[0], 1);
  }

  if (verbose) {
    fprintf(stderr, "%s: %s ENTER\n", argv[0], inputFrameFeaturesFileName);
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Acquire output stream
  FILE* outputFp = stdout;
  if (outputFeatureVectorsFileName != nullptr) {
    outputFp = facebook::tmk::io::openFileOrDie(
        outputFeatureVectorsFileName, (char*)"wb", argv[0]);
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Read input header
  io::FrameFeaturesFileHeader inputFeatHeader;
  io::TMKFramewiseAlgorithm algorithm;
  if (!facebook::tmk::io::readFrameFeaturesFileHeader(
          inputFp, &inputFeatHeader, algorithm, argv[0])) {
    // error message already printed out.
    exit(1);
  }

  if (algorithm == io::TMKFramewiseAlgorithm::UNRECOGNIZED) {
    io::reportUnrecognizedAlgorithmMagic(
        argv[0],
        inputFeatHeader.frameFeatureAlgorithmMagic,
        inputFrameFeaturesFileName);
    exit(1);
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  if (verbose) {
    fprintf(
        stderr,
        "frameFeatureDimension %d\n",
        inputFeatHeader.frameFeatureDimension);
    fprintf(
        stderr, "framesPerSecond       %d\n", inputFeatHeader.framesPerSecond);
  }

  int frameFeatureDimension = inputFeatHeader.frameFeatureDimension;
  int framesPerSecond = inputFeatHeader.framesPerSecond;

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // TODO(t25190142): run the Baraldi Python code and learn optimal
  // parameters.
  facebook::tmk::algo::Periods periods =
      TMKFeatureVectors::makePoullotPeriods();
  facebook::tmk::algo::FourierCoefficients fourierCoefficients =
      TMKFeatureVectors::makePoullotFourierCoefficients();

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  TMKFeatureVectors tmkFeatureVectors(
      algorithm,
      framesPerSecond,
      periods,
      fourierCoefficients,
      frameFeatureDimension);

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  facebook::tmk::algo::FrameFeature frameFeature(frameFeatureDimension);
  int frameNumber = 0;
  bool eof = false;
  for (frameNumber = 0;; frameNumber++) {
    bool read_rc =
        facebook::tmk::io::readFloatVector(frameFeature, inputFp, eof);
    if (eof) {
      break;
    }
    if (!read_rc) {
      fprintf(
          stderr,
          "%s: failed to read frame feature %d.\n",
          argv[0],
          frameNumber);
      return 1;
    }

    if (verbose) {
      if ((frameNumber % 100) == 0) {
        fprintf(stderr, "%s: fno %d\n", argv[0], frameNumber);
      }
    }

    tmkFeatureVectors.ingestFrameFeature(frameFeature, frameNumber);
  }

  tmkFeatureVectors.finishFrameFeatureIngest();

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  if (!tmkFeatureVectors.writeToOutputStream(outputFp, argv[0])) {
    perror("fwrite");
    fprintf(stderr, "%s: could not write feature-vectors.\n", argv[0]);
    return 1;
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  if (outputFp != stdout) {
    fclose(outputFp);
  }

  if (verbose) {
    fprintf(stderr, "%s: %s EXIT\n", argv[0], inputFrameFeaturesFileName);
  }

  return 0;
}
