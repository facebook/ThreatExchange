// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
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
#include <tmk/cpp/bin/tmk_default_thresholds.h>
#include <tmk/cpp/io/tmkio.h>

#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <chrono>
#include <set>
#include <unordered_map>

using namespace facebook::tmk;
using namespace facebook::tmk::algo;

void handleInputFileNameOrDie(
    const char* argv0,
    const char* tmkFileName,
    std::unordered_map<std::string, std::shared_ptr<TMKFeatureVectors>>&
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
      fp,
      "--include-self: Match each hash against itself as well as others.\n");
  fprintf(fp, "-v|--verbose: Be more verbose.\n");

  exit(exit_rc);
}

// ================================================================
int main(int argc, char** argv) {
  bool fileNamesFromStdin = false;
  float c1 = DEFAULT_LEVEL_1_THRESHOLD;
  float c2 = DEFAULT_LEVEL_2_THRESHOLD;
  bool includeSelf = false;
  bool verbose = false;

  int argi = 1;
  while ((argi < argc) && argv[argi][0] == '-') {
    char* flag = argv[argi++];
    if (!strcmp(flag, "-h") || !strcmp(flag, "--help")) {
      usage(argv[0], 0);

    } else if (!strcmp(flag, "-i")) {
      fileNamesFromStdin = true;
    } else if (!strcmp(flag, "-v") || !strcmp(flag, "--verbose")) {
      verbose = true;

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
  std::unordered_map<std::string, std::shared_ptr<TMKFeatureVectors>>
      metadataToFeatures;
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

  std::chrono::time_point<std::chrono::system_clock> startScores =
      std::chrono::system_clock::now();

  if (verbose) {
    printf("\n");
    printf("CALCULATING THE SCORES\n");
  }

  std::vector<std::string> filenames;
  filenames.reserve(metadataToFeatures.size());

  for (const auto& s : metadataToFeatures)
    filenames.push_back(s.first);

  int selfOffset = includeSelf ? 0 : 1;

#pragma omp parallel for schedule(dynamic)
  for (unsigned int i = 0; i < filenames.size() - selfOffset; i++) {
    for (unsigned int j = i + selfOffset; j < filenames.size(); j++) {
      bool flip = filenames[i] > filenames[j];
      const std::string& filename1 = flip ? filenames[j] : filenames[i];
      const std::string& filename2 = flip ? filenames[i] : filenames[j];

      const std::shared_ptr<TMKFeatureVectors> pfv1 =
          metadataToFeatures.at(filename1);
      const std::shared_ptr<TMKFeatureVectors> pfv2 =
          metadataToFeatures.at(filename2);

      if (!TMKFeatureVectors::areCompatible(*pfv1, *pfv2)) {
        fprintf(
            stderr,
            "%s: immiscible provenances:\n%s\n%s\n",
            argv[0],
            filename1.c_str(),
            filename2.c_str());
        exit(1);
      }

      float s1 = TMKFeatureVectors::computeLevel1Score(*pfv1, *pfv2);
      if (s1 >= c1) {
        float s2 = TMKFeatureVectors::computeLevel2Score(*pfv1, *pfv2);
        printf(
            "%.6f %.6f %s %s\n", s1, s2, filename1.c_str(), filename2.c_str());
      }
    }
  } // end parallel

  std::chrono::time_point<std::chrono::system_clock> endScores =
      std::chrono::system_clock::now();
  std::chrono::duration<double> scoresSeconds = endScores - startScores;
  if (verbose) {
    printf("\n");
    printf("SCORES SECONDS = %.6lf\n", scoresSeconds.count());
  }

  return 0;
}

// ----------------------------------------------------------------
void handleInputFileNameOrDie(
    const char* argv0,
    const char* tmkFileName,
    std::unordered_map<std::string, std::shared_ptr<TMKFeatureVectors>>&
        metadataToFeatures) {
  std::shared_ptr<TMKFeatureVectors> pfv =
      TMKFeatureVectors::readFromInputFile(tmkFileName, argv0);

  if (pfv == nullptr) {
    fprintf(stderr, "%s: failed to read \"%s\".\n", argv0, tmkFileName);
    exit(1);
  }

  metadataToFeatures[std::string(tmkFileName)] = pfv;
}
