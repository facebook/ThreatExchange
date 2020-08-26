// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

// ================================================================
// Two-level scoring of video pairs.
//
// * Given a single 'needle' featurized video and a list of 'haystack'
//   featurized videos.
//
// * Looking at the time-average feature using cosine similarity (score in the
//   range [-1,1]) is quick and culls the full haystack down to a short list.
//   (For this initial concept-code, at the moment, this is a linear scan of
//   the haystack list -- but this could be an indexed lookup.)
//
// * Given the short list, looking at the score (in the [0-1]) further
//   reduces the list to declare matches.
//
// * This is a quick way to look for similar videos within a collection.  For
// this executable, the 'needles' and 'haystack' lists are the same; this needs
// adapation to allow those to be separate lists.
// ================================================================

#include <tmk/cpp/algo/tmkfv.h>
#include <tmk/cpp/io/tmkio.h>
#include <tmk/cpp/bin/tmk_default_thresholds.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <map>
#include <set>

using namespace facebook::tmk;
using namespace facebook::tmk::algo;

void handleInputFileNameOrDie(
    const char* argv0,
    const char* tmkFileName,
    std::map<std::string, std::shared_ptr<TMKFeatureVectors>>&
        metadataToFeatures);

// ================================================================
void usage(const char* argv0, int exit_rc) {
  FILE* fp = (exit_rc == 0) ? stdout : stderr;
  fprintf(fp, "Usage: %s [options] [input file name]\n", argv0);
  fprintf(fp, "Options:\n");
  fprintf(
      fp,
      "-i:       Take feature-vector-file names from stdin, "
      "not argv.\n");
  fprintf(
      fp,
      "--c1 {x}: Level-1 threshold: default %.3f.\n",
      DEFAULT_LEVEL_1_THRESHOLD);
  fprintf(
      fp,
      "--c2 {y}: Level-2 threshold: default %.3f.\n",
      DEFAULT_LEVEL_2_THRESHOLD);
  fprintf(
      fp, "--include-self: Match each hash against itself as well as others.\n");
  exit(exit_rc);
}

// ================================================================
int main(int argc, char** argv) {
  bool fileNamesFromStdin = false;
  float c1 = DEFAULT_LEVEL_1_THRESHOLD;
  float c2 = DEFAULT_LEVEL_2_THRESHOLD;
  bool includeSelf = false;

  int argi = 1;
  while ((argi < argc) && argv[argi][0] == '-') {
    char* flag = argv[argi++];
    if (!strcmp(flag, "-h") || !strcmp(flag, "--help")) {
      usage(argv[0], 0);

    } else if (!strcmp(flag, "-i")) {
      fileNamesFromStdin = true;

    } else if (!strcmp(flag, "--c1")) {
      if (argi >= argc) {
        usage(argv[0], 1);
      }
      if (sscanf(argv[argi], "%f", &c1) != 1) {
        usage(argv[0], 1);
      }
      argi++;
    } else if (!strcmp(flag, "--c2")) {
      if (argi >= argc) {
        usage(argv[0], 1);
      }
      if (sscanf(argv[argi], "%f", &c2) != 1) {
        usage(argv[0], 1);
      }
      argi++;

    } else if (!strcmp(flag, "--include-self")) {
      includeSelf = true;

    } else {
      usage(argv[0], 1);
    }
  }
  if (fileNamesFromStdin) {
    if (argi < argc) {
      fprintf(
          stderr, "%s: -i is incompatible with filename argument.\n", argv[0]);
      exit(1);
    }
  } else {
    if (argi >= argc) {
      fprintf(
          stderr,
          "%s: without -i, one or more filename arguments are required.\n",
          argv[0]);
      exit(1);
    }
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // LOAD FEATURES
  std::map<std::string, std::shared_ptr<TMKFeatureVectors>> metadataToFeatures;
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
      handleInputFileNameOrDie(argv[0], tmkFileName, metadataToFeatures);
    }
  } else {
    for (; argi < argc; argi++) {
      char* tmkFileName = argv[argi];
      handleInputFileNameOrDie(argv[0], tmkFileName, metadataToFeatures);
    }
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // COMPUTE AND PRINT SCORES
  for (const auto& it1 : metadataToFeatures) {
    const std::string& metadata1 = it1.first;
    std::shared_ptr<TMKFeatureVectors> pfv1 = it1.second;

    for (const auto& it2 : metadataToFeatures) {
      const std::string& metadata2 = it2.first;
      std::shared_ptr<TMKFeatureVectors> pfv2 = it2.second;

      if (!TMKFeatureVectors::areCompatible(*pfv1, *pfv2)) {
        fprintf(
            stderr,
            "%s: immiscible provenances:\n%s\n%s\n",
            argv[0],
            metadata1.c_str(),
            metadata2.c_str());
        exit(1);
      }

      // Don't compare videos to themselves; don't do comparisons twice
      // (A vs. B, then B vs. A).
      bool skipThisPair =
          includeSelf ? metadata1 > metadata2 : metadata1 >= metadata2;
      if (skipThisPair) {
        continue;
      }

      float s1 = TMKFeatureVectors::computeLevel1Score(*pfv1, *pfv2);
      if (s1 >= c1) {
        float s2 = TMKFeatureVectors::computeLevel2Score(*pfv1, *pfv2);
        printf(
            "%.6f %.6f %s %s\n", s1, s2, metadata1.c_str(), metadata2.c_str());
      }
    }
  }

  return 0;
}

// ----------------------------------------------------------------
void handleInputFileNameOrDie(
    const char* argv0,
    const char* tmkFileName,
    std::map<std::string, std::shared_ptr<TMKFeatureVectors>>&
        metadataToFeatures) {
  std::shared_ptr<TMKFeatureVectors> pfv =
      TMKFeatureVectors::readFromInputFile(tmkFileName, argv0);

  if (pfv == nullptr) {
    fprintf(stderr, "%s: failed to read \"%s\".\n", argv0, tmkFileName);
    exit(1);
  }

  metadataToFeatures[std::string(tmkFileName)] = pfv;
}
