// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

#include <tmk/cpp/algo/tmkfv.h>
#include <tmk/cpp/io/tmkio.h>
#include <tmk/cpp/bin/tmk_default_thresholds.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <chrono>
#include <map>
#include <set>

using namespace facebook::tmk;
using namespace facebook::tmk::algo;

void handleListFileNameOrDie(
    const char* argv0,
    const char* listFileName,
    std::map<std::string, std::shared_ptr<TMKFeatureVectors>>&
        metadataToFeatures);

void handleListFpOrDie(
    const char* argv0,
    FILE* listFp,
    std::map<std::string, std::shared_ptr<TMKFeatureVectors>>&
        metadataToFeatures);

void handletmkFileNameOrDie(
    const char* argv0,
    const char* tmkFileName,
    std::map<std::string, std::shared_ptr<TMKFeatureVectors>>&
        metadataToFeatures);

// ================================================================
void usage(char* argv0, int exit_rc) {
  FILE* fp = (exit_rc == 0) ? stdout : stderr;
  fprintf(
      fp,
      "Usage: %s [options] [needles file name] {haystack file name}\n",
      argv0);
  fprintf(
      fp,
      "Needles file and haystack file should each contain .tmk file names,\n"
      "one per line. Then the haystack .tmk files are loaded into memory.\n"
      "Then each needle .tmk file is queried against the haystack, and all\n"
      "matches within specified level-1/level-2 thresholds are printed.\n");
  fprintf(fp, "Options:\n");
  fprintf(fp, "-v|--verbose: Be more verbose.\n");
  fprintf(
      fp,
      "--c1 {x}: Level-1 threshold: default %.3f.\n",
      FULL_DEFAULT_LEVEL_1_THRESHOLD);
  fprintf(
      fp,
      "--c2 {y}: Level-2 threshold: default %.3f.\n",
      FULL_DEFAULT_LEVEL_2_THRESHOLD);
  exit(exit_rc);
}

// ================================================================
int main(int argc, char** argv) {
  bool verbose = false;
  float c1 = FULL_DEFAULT_LEVEL_1_THRESHOLD;
  float c2 = FULL_DEFAULT_LEVEL_2_THRESHOLD;

  int argi = 1;
  while ((argi < argc) && argv[argi][0] == '-') {
    char* flag = argv[argi++];
    if (!strcmp(flag, "-h") || !strcmp(flag, "--help")) {
      usage(argv[0], 0);
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

    } else {
      usage(argv[0], 1);
    }
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // LOAD FEATURES
  std::chrono::time_point<std::chrono::system_clock> startLoad =
      std::chrono::system_clock::now();

  std::map<std::string, std::shared_ptr<TMKFeatureVectors>>
      needlesMetadataToFeatures;
  std::map<std::string, std::shared_ptr<TMKFeatureVectors>>
      haystackMetadataToFeatures;

  if ((argc - argi) == 1) {
    handleListFpOrDie(argv[0], stdin, needlesMetadataToFeatures);
    handleListFileNameOrDie(argv[0], argv[argi], haystackMetadataToFeatures);
  } else if ((argc - argi) == 2) {
    handleListFileNameOrDie(argv[0], argv[argi], needlesMetadataToFeatures);
    handleListFileNameOrDie(
        argv[0], argv[argi + 1], haystackMetadataToFeatures);
  } else {
    usage(argv[0], 1);
    exit(1);
  }

  std::chrono::time_point<std::chrono::system_clock> endLoad =
      std::chrono::system_clock::now();
  std::chrono::duration<double> loadSeconds = endLoad - startLoad;
  if (verbose) {
    printf("LOAD SECONDS   = %.3lf\n", loadSeconds.count());
    printf("NEEDLES COUNT  = %d\n", (int)needlesMetadataToFeatures.size());
    printf("HAYSTACK COUNT = %d\n", (int)haystackMetadataToFeatures.size());
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // SANITY-CHECK (OMITTABLE FOR PRODUCTION ONCE WE SETTLE ON ONE FRAMEWISE
  // ALGORITHM)
  std::chrono::time_point<std::chrono::system_clock> startCheck =
      std::chrono::system_clock::now();
  for (const auto& it1 : needlesMetadataToFeatures) {
    const std::string& metadata1 = it1.first;
    std::shared_ptr<TMKFeatureVectors> pfv1 = it1.second;

    for (const auto& it2 : haystackMetadataToFeatures) {
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
    }
  }

  std::chrono::time_point<std::chrono::system_clock> endCheck =
      std::chrono::system_clock::now();
  std::chrono::duration<double> checkSeconds = endCheck - startCheck;
  if (verbose) {
    printf("\n");
    printf("CHECK SECONDS = %.3lf\n", checkSeconds.count());
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // QUERY
  std::chrono::time_point<std::chrono::system_clock> startQuery =
      std::chrono::system_clock::now();
  for (const auto& it1 : needlesMetadataToFeatures) {
    const std::string& metadata1 = it1.first;
    std::shared_ptr<TMKFeatureVectors> pfv1 = it1.second;

    if (verbose) {
      printf("\n");
      printf("QUERY FOR %s\n", metadata1.c_str());
    }

    for (const auto& it2 : haystackMetadataToFeatures) {
      const std::string& metadata2 = it2.first;
      std::shared_ptr<TMKFeatureVectors> pfv2 = it2.second;

      float s1 = TMKFeatureVectors::computeLevel1Score(*pfv1, *pfv2);
      if (s1 >= c1) {
        float s2 = TMKFeatureVectors::computeLevel2Score(*pfv1, *pfv2);
        if (s2 >= c2) {
          if (verbose) {
            printf("  %.6f %.6f %s\n", s1, s2, metadata2.c_str());
          } else {
            printf(
                "%.6f %.6f %s %s\n",
                s1,
                s2,
                metadata1.c_str(),
                metadata2.c_str());
          }
        }
      }
    }
  }

  std::chrono::time_point<std::chrono::system_clock> endQuery =
      std::chrono::system_clock::now();
  std::chrono::duration<double> querySeconds = endQuery - startQuery;
  if (verbose) {
    printf("\n");
    printf("QUERY SECONDS = %.6lf\n", querySeconds.count());
    printf(
        "MEAN QUERY SECONDS = %.6lf\n",
        querySeconds.count() / needlesMetadataToFeatures.size());
  }

  return 0;
}

// ----------------------------------------------------------------
void handleListFileNameOrDie(
    const char* argv0,
    const char* listFileName,
    std::map<std::string, std::shared_ptr<TMKFeatureVectors>>&
        metadataToFeatures) {
  FILE* fp = fopen(listFileName, "r");
  if (fp == nullptr) {
    perror("fopen");
    fprintf(
        stderr, "%s: could not open \"%s\" for read.\n", argv0, listFileName);
    exit(1);
  }

  handleListFpOrDie(argv0, fp, metadataToFeatures);

  fclose(fp);
}

// ----------------------------------------------------------------
void handleListFpOrDie(
    const char* argv0,
    FILE* listFp,
    std::map<std::string, std::shared_ptr<TMKFeatureVectors>>&
        metadataToFeatures) {
  char* tmkFileName = nullptr;
  size_t linelen = 0;
  while ((ssize_t)(linelen = getline(&tmkFileName, &linelen, listFp)) != -1) {
    // Chomp
    if (linelen > 0) {
      if (tmkFileName[linelen - 1] == '\n') {
        tmkFileName[linelen - 1] = 0;
      }
    }
    handletmkFileNameOrDie(argv0, tmkFileName, metadataToFeatures);
  }
}

// ----------------------------------------------------------------
void handletmkFileNameOrDie(
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

  pfv->L2NormalizePureAverageFeature();

  metadataToFeatures[std::string(tmkFileName)] = pfv;
}
