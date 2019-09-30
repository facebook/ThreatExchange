// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

// ================================================================
// Ops tool for visualizing output of step 2 of the TMK 3-stage
// hashing pipeline:
//
// * vid2vstr (or ffmpeg.exe): .mp4 file to .vstr decoded stream
// * vstr2feat: .vstr file to .feat list of frame-featue vectors
// * feat2tmk: .feat file to .tmk list of TMK cosine/sine features
//
// The format is suitable for various ad-hoc processing in Python
// or what have you.
// ================================================================

#include <tmk/cpp/io/tmkio.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

using namespace facebook::tmk;

// ================================================================
void usage(char* argv0, int exit_rc) {
  FILE* fp = (exit_rc == 0) ? stdout : stderr;
  fprintf(fp, "Usage: %s [options] [input .feat file name]\n", argv0);
  fprintf(fp, "If the input .feat file name is omitted, stdin is read.\n");
  fprintf(fp, "Options:\n");
  fprintf(fp, "--output-feature-vectors-file-name {x}\n");
  fprintf(fp, "-v|--verbose\n");
  fprintf(fp, "-r|--raw: Print only numbers and whitespace, no filenames.\n");
  exit(exit_rc);
}

// ================================================================
int main(int argc, char** argv) {
  char* outputFeatureVectorsFileName = nullptr;
  bool verbose = false;
  bool raw = false;

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Parse command line
  int argi = 1;
  while ((argi < argc) && argv[argi][0] == '-') {
    char* flag = argv[argi++];
    if (!strcmp(flag, "-h") || !strcmp(flag, "--help")) {
      usage(argv[0], 0);

    } else if (!strcmp(flag, "-v") || !strcmp(flag, "--verbose")) {
      verbose = true;
    } else if (!strcmp(flag, "-r") || !strcmp(flag, "--raw")) {
      raw = true;
    } else if (!strcmp(flag, "--output-feature-vectors-file-name")) {
      if ((argc - argi) < 1) {
        usage(argv[0], 1);
      }
      outputFeatureVectorsFileName = argv[argi++];

    } else {
      usage(argv[0], 1);
    }
  }

  FILE* inputFp = stdin;
  if (argi == argc) {
    // keep stdin
  } else if ((argc - argi) == 1) {
    char* inputFrameFeaturesFileName = argv[argi];
    inputFp = facebook::tmk::io::openFileOrDie(
        inputFrameFeaturesFileName, (char*)"rb", argv[0]);
  } else {
    usage(argv[0], 1);
  }
  FILE* outputFp = stdout;
  if (outputFeatureVectorsFileName != nullptr) {
    outputFp = facebook::tmk::io::openFileOrDie(
        outputFeatureVectorsFileName, (char*)"rb", argv[0]);
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

  if (verbose) {
    fprintf(
        stderr,
        "frameFeatureDimension %d\n",
        inputFeatHeader.frameFeatureDimension);
    fprintf(
        stderr, "framesPerSecond       %d\n", inputFeatHeader.framesPerSecond);
    fprintf(
        stderr,
        "algorithm             %s\n",
        facebook::tmk::io::algorithmToName(algorithm).c_str());
  }

  int frameFeatureDimension = inputFeatHeader.frameFeatureDimension;

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  std::vector<float> frameFeature(frameFeatureDimension);
  int frameNumber = 0;
  bool eof = false;
  for (frameNumber = 0;; frameNumber++) {
    int read_rc =
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

    if (raw) {
      for (int i = 0; i < frameFeatureDimension; i++) {
        printf(" %f", frameFeature[i]);
      }
      printf("\n");
    } else {
      printf("fno=%d", frameNumber);
      for (int i = 0; i < frameFeatureDimension; i++) {
        printf(",%f", frameFeature[i]);
      }
      printf("\n");
    }
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  if (inputFp != stdin) {
    fclose(inputFp);
  }
  if (outputFp != stdout) {
    fclose(outputFp);
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  return 0;
}
