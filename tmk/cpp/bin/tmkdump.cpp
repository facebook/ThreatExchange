// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

// ================================================================
// Ops tool for visualizing output of step 3 of the TMK 3-stage
// hashing pipeline:
//
// * vid2vstr (or ffmpeg.exe): .mp4 file to .vstr decoded stream
// * vstr2feat: .vstr file to .feat list of frame-featue vectors
// * feat2tmk: .feat file to .tmk list of TMK cosine/sine features
//
// The format is suitable for various ad-hoc processing in Python
// or what have you.
//
// Example use with -i:
// $ find ~/tmk/tmk/pdqf -type f -name '*.tmk' | tmkdump -i --avg-only
// ================================================================

#include <tmk/cpp/algo/tmkfv.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

using namespace facebook::tmk;
using namespace facebook::tmk::algo;

void handleInputFileNameOrDie(
    const char* argv0,
    const char* tmkFileName,
    bool printAvgOnly,
    bool raw);

int handleInputFp(
    const char* argv0,
    const char* tmkFileName,
    FILE* inputFp,
    bool printAvgOnly,
    bool raw);

int handleInputFpRaw(
    const char* argv0,
    const char* tmkFileName,
    FILE* inputFp,
    bool printAvgOnly);

int handleInputFpNonRaw(
    const char* argv0,
    const char* tmkFileName,
    FILE* inputFp,
    bool printAvgOnly);

// ================================================================
void usage(char* argv0, int exit_rc) {
  FILE* fp = (exit_rc == 0) ? stdout : stderr;
  fprintf(fp, "Usage: %s [options] [input file name]\n", argv0);
  fprintf(fp, "Options:\n");
  fprintf(fp, "--avg-only: Do not print cos/sin feature vectors.\n");
  fprintf(
      fp,
      "-i:         Take feature-vector-file names from stdin, "
      "not argv.\n");
  fprintf(fp, "-r|--raw:   Print only numbers and whitespace, no filenames.\n");
  exit(exit_rc);
}

// ================================================================
int main(int argc, char** argv) {
  bool printAvgOnly = false;
  bool fileNamesFromStdin = false;
  bool raw = false;

  int argi = 1;
  while ((argi < argc) && argv[argi][0] == '-') {
    char* flag = argv[argi++];
    if (!strcmp(flag, "-h") || !strcmp(flag, "--help")) {
      usage(argv[0], 0);
    } else if (!strcmp(flag, "-r") || !strcmp(flag, "--raw")) {
      raw = true;

    } else if (!strcmp(flag, "--avg-only")) {
      printAvgOnly = true;

    } else if (!strcmp(flag, "-i")) {
      fileNamesFromStdin = true;

    } else {
      usage(argv[0], 1);
    }
  }
  if (fileNamesFromStdin && (argi < argc)) {
    fprintf(
        stderr, "%s: -i is incompatible with filename argument.\n", argv[0]);
    exit(1);
  }

  if (fileNamesFromStdin) {
    char* tmkFileName = nullptr;
    size_t linelen = 0;

    while ((ssize_t)(linelen = getline(&tmkFileName, &linelen, stdin)) != -1) {
      // Chomp
      if (linelen > 0) {
        if (tmkFileName[linelen - 1] == '\n') {
          tmkFileName[linelen - 1] = 0;
        }
      }

      handleInputFileNameOrDie(argv[0], tmkFileName, printAvgOnly, raw);
    }

  } else {
    if (argi >= argc) {
      handleInputFp(argv[0], (char*)"(stdin)", stdin, printAvgOnly, raw);
    } else {
      for (; argi < argc; argi++) {
        char* tmkFileName = argv[argi];
        handleInputFileNameOrDie(argv[0], tmkFileName, printAvgOnly, raw);
      }
    }
  }

  return 0;
}

// ----------------------------------------------------------------
void handleInputFileNameOrDie(
    const char* argv0,
    const char* tmkFileName,
    bool printAvgOnly,
    bool raw) {
  FILE* inputFp =
      facebook::tmk::io::openFileOrDie(tmkFileName, (char*)"rb", argv0);
  handleInputFp(argv0, tmkFileName, inputFp, printAvgOnly, raw);
  fclose(inputFp);
}

// ----------------------------------------------------------------
int handleInputFp(
    const char* argv0,
    const char* tmkFileName,
    FILE* inputFp,
    bool printAvgOnly,
    bool raw) {
  return raw ? handleInputFpRaw(argv0, tmkFileName, inputFp, printAvgOnly)
             : handleInputFpNonRaw(argv0, tmkFileName, inputFp, printAvgOnly);
}

// ----------------------------------------------------------------
int handleInputFpRaw(
    const char* argv0,
    const char* tmkFileName,
    FILE* inputFp,
    bool printAvgOnly) {
  std::shared_ptr<TMKFeatureVectors> pfv =
      TMKFeatureVectors::readFromInputStream(inputFp, argv0);

  if (pfv == nullptr) {
    fprintf(stderr, "%s: failed to read \"%s\".\n", argv0, tmkFileName);
    // error message already printed out?
    exit(1);
  }

  int frameFeatureDimension = pfv->getFrameFeatureDimension();

  facebook::tmk::algo::FrameFeature pureAverageFeature =
      pfv->getPureAverageFeature();
  for (int k = 0; k < frameFeatureDimension; k++) {
    printf(" %.6e", pureAverageFeature[k]);
  }
  printf("\n");

  if (!printAvgOnly) {
    facebook::tmk::algo::Periods periods = pfv->getPeriods();
    facebook::tmk::algo::FeaturesByPeriodsAndFourierCoefficients cosFeatures =
        pfv->getCosFeatures();
    facebook::tmk::algo::FeaturesByPeriodsAndFourierCoefficients sinFeatures =
        pfv->getCosFeatures();

    for (int i = 0; i < pfv->getNumPeriods(); i++) {
      for (int j = 0; j < pfv->getNumFourierCoefficients(); j++) {
        for (int k = 0; k < frameFeatureDimension; k++) {
          printf(" %.6e", cosFeatures[i][j][k]);
        }
        printf("\n");
      }
    }

    for (int i = 0; i < pfv->getNumPeriods(); i++) {
      for (int j = 0; j < pfv->getNumFourierCoefficients(); j++) {
        for (int k = 0; k < frameFeatureDimension; k++) {
          printf(" %.6e", sinFeatures[i][j][k]);
        }
        printf("\n");
      }
    }
  }

  return 0;
}

// ----------------------------------------------------------------
int handleInputFpNonRaw(
    const char* argv0,
    const char* tmkFileName,
    FILE* inputFp,
    bool printAvgOnly) {
  std::shared_ptr<TMKFeatureVectors> pfv =
      TMKFeatureVectors::readFromInputStream(inputFp, argv0);

  if (pfv == nullptr) {
    fprintf(stderr, "%s: failed to read \"%s\".\n", argv0, tmkFileName);
    // error message already printed out?
    exit(1);
  }

  int framesPerSecond = pfv->getFramesPerSecond();
  int frameFeatureDimension = pfv->getFrameFeatureDimension();
  int frameFeatureCount = pfv->getFrameFeatureCount();
  facebook::tmk::io::TMKFramewiseAlgorithm algo = pfv->getAlgorithm();
  fprintf(stdout, "frameFeatureDimension       %d\n", frameFeatureDimension);
  fprintf(stdout, "framesPerSecond             %d\n", framesPerSecond);
  fprintf(stdout, "frameFeatureCount           %d\n", frameFeatureCount);
  fprintf(
      stdout,
      "algorithm                   %s\n",
      facebook::tmk::io::algorithmToName(algo).c_str());

  printf("%s", tmkFileName);
  facebook::tmk::algo::FrameFeature pureAverageFeature =
      pfv->getPureAverageFeature();
  for (int k = 0; k < frameFeatureDimension; k++) {
    printf(",%.6e", pureAverageFeature[k]);
  }
  printf("\n");

  if (!printAvgOnly) {
    facebook::tmk::algo::Periods periods = pfv->getPeriods();
    facebook::tmk::algo::FeaturesByPeriodsAndFourierCoefficients cosFeatures =
        pfv->getCosFeatures();
    facebook::tmk::algo::FeaturesByPeriodsAndFourierCoefficients sinFeatures =
        pfv->getSinFeatures();

    for (int i = 0; i < pfv->getNumPeriods(); i++) {
      for (int j = 0; j < pfv->getNumFourierCoefficients(); j++) {
        printf("%s:%d:%d:cos", tmkFileName, periods[i], j);
        for (int k = 0; k < frameFeatureDimension; k++) {
          printf(",%.6e", cosFeatures[i][j][k]);
        }
        printf("\n");
      }
    }

    for (int i = 0; i < pfv->getNumPeriods(); i++) {
      for (int j = 0; j < pfv->getNumFourierCoefficients(); j++) {
        printf("%s:%d:%d:sin", tmkFileName, periods[i], j);
        for (int k = 0; k < frameFeatureDimension; k++) {
          printf(",%.6e", sinFeatures[i][j][k]);
        }
        printf("\n");
      }
    }
  }

  return 0;
}
