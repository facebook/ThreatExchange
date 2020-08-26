// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

// ================================================================
// Given a collection of TMK hashes this reduces it to a subset containing
// only one per cluster, at user-specified distance.
//
// Note: this is distinct from tmk-clusterize.cpp which coalesces overlapping
// hyperspheres. This program does not do so.
//
// It uses no indexing so it requires O(MN) cosine-similarity computations
// between hashes where N is the number of inputs and M is the number of
// cluster-centers found.  Nonetheless it runs on over 1000 feature-vector
// files in just a few seconds.
// ================================================================

#include <tmk/cpp/algo/tmkfv.h>
#include <tmk/cpp/io/tmkio.h>
#include <tmk/cpp/bin/tmk_default_thresholds.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <cassert>
#include <map>
#include <set>

using namespace facebook::tmk;
using namespace facebook::tmk::algo;

void ingestFeatures(
    std::map<std::string, int>& repsWithCounts,
    float c1,
    float c2,
    char* argv0,
    int verboseCount,
    bool level1Only);

std::shared_ptr<TMKFeatureVectors> loadFromInputFileNameOrDie(
    const char* argv0,
    const char* tmkFileName);

void printTextOutput(const std::map<std::string, int>& repsWithCounts);

// ================================================================
void usage(char* argv0, int exit_rc) {
  FILE* fp = (exit_rc == 0) ? stdout : stderr;
  fprintf(fp, "Usage: %s [options]\n", argv0);
  fprintf(
      fp, "Paths to .tmk files must appear one per line on standard input.\n");
  fprintf(fp, "Options:\n");
  fprintf(fp, "--avg-only: Do not print cos/sin feature vectors.\n");
  fprintf(fp, "-s:         Print a blank line between similarity clusters.\n");
  fprintf(
      fp, "-v {n}: Print ingested .tmk file names to stderr every nth file.\n");
  fprintf(
      fp,
      "--c1 {x}: Level-1 threshold: default %.3f.\n",
      DEFAULT_LEVEL_1_THRESHOLD);
  fprintf(
      fp,
      "--c2 {y}: Level-2 threshold: default %.3f.\n",
      DEFAULT_LEVEL_2_THRESHOLD);
  fprintf(fp, "--level-1-only: Don't do level-2 thresholding (runs faster).\n");
  exit(exit_rc);
}

// ================================================================
int main(int argc, char** argv) {
  float c1 = DEFAULT_LEVEL_1_THRESHOLD;
  float c2 = DEFAULT_LEVEL_2_THRESHOLD;
  bool level1Only = false;
  int verboseCount = 0;

  int argi = 1;
  while ((argi < argc) && argv[argi][0] == '-') {
    char* flag = argv[argi++];
    if (!strcmp(flag, "-h") || !strcmp(flag, "--help")) {
      usage(argv[0], 0);

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

    } else if (!strcmp(flag, "--level-1-only")) {
      level1Only = true;
      argi++;

    } else if (!strcmp(flag, "-v")) {
      if (argi >= argc) {
        usage(argv[0], 1);
      }
      if (sscanf(argv[argi], "%d", &verboseCount) != 1) {
        usage(argv[0], 1);
      }
      argi++;

    } else {
      usage(argv[0], 1);
    }
  }
  if (argi < argc) {
    fprintf(stderr, "%s: extraneous argument \"%s\".\n", argv[0], argv[argi]);
    exit(1);
  }

  std::map<std::string, int> repsWithCounts;

  ingestFeatures(repsWithCounts, c1, c2, argv[0], verboseCount, level1Only);

  printTextOutput(repsWithCounts);

  return 0;
}

// ----------------------------------------------------------------
void ingestFeatures(
    std::map<std::string, int>& repsWithCounts,
    float c1,
    float c2,
    char* argv0,
    int verboseCount,
    bool level1Only) {
  std::map<std::string, std::shared_ptr<TMKFeatureVectors>>
      repMetadataToFeatures;
  int ingestCounter = 0;

  char* ptmkFileName = nullptr;
  size_t linelen = 0;

  while ((ssize_t)(linelen = getline(&ptmkFileName, &linelen, stdin)) != -1) {
    // Chomp
    if (linelen > 0) {
      if (ptmkFileName[linelen - 1] == '\n') {
        ptmkFileName[linelen - 1] = 0;
      }
    }
    std::string tmkFileName = std::string(ptmkFileName);

    // Read TMK file
    ingestCounter++;
    if (verboseCount > 0) {
      if ((ingestCounter % verboseCount) == 0) {
        fprintf(stderr, "... %d\n", ingestCounter);
      }
    }
    std::shared_ptr<TMKFeatureVectors> pfv =
        loadFromInputFileNameOrDie(argv0, ptmkFileName);
    assert(pfv != nullptr); // Guaranteed by loadFromInputFileNameOrDie

    // Search
    bool isNewRepresentative = true;
    for (auto& repIter : repMetadataToFeatures) {
      const std::string& repFileName = repIter.first;
      const std::shared_ptr<TMKFeatureVectors> pfvr = repIter.second;

      if (!TMKFeatureVectors::areCompatible(*pfv, *pfvr)) {
        fprintf(
            stderr,
            "%s: immiscible provenances:\n%s\n%s\n",
            argv0,
            tmkFileName.c_str(),
            repFileName.c_str());
        exit(1);
      }
      float s1 = TMKFeatureVectors::computeLevel1Score(*pfv, *pfvr);

      bool matchesThisRep = false;
      if (s1 >= c1) {
        if (level1Only) {
          matchesThisRep = true;
        } else {
          float s2 = TMKFeatureVectors::computeLevel2Score(*pfv, *pfvr);
          if (s2 >= c2) {
            matchesThisRep = true;
          }
        }
      }

      if (matchesThisRep) {
        isNewRepresentative = false;
        repsWithCounts[repFileName]++;
        break;
      }
    }

    // Update
    if (isNewRepresentative) {
      repsWithCounts[tmkFileName] = 1;
      repMetadataToFeatures[tmkFileName] = pfv;
    }
  }
}

// ----------------------------------------------------------------
std::shared_ptr<TMKFeatureVectors> loadFromInputFileNameOrDie(
    const char* argv0,
    const char* tmkFileName) {
  FILE* inputFp =
      facebook::tmk::io::openFileOrDie(tmkFileName, (char*)"rb", argv0);

  std::shared_ptr<TMKFeatureVectors> pfv =
      TMKFeatureVectors::readFromInputStream(inputFp, argv0);

  if (pfv == nullptr) {
    fprintf(stderr, "%s: failed to read \"%s\".\n", argv0, tmkFileName);
    // error message already printed out?
    exit(1);
  }

  fclose(inputFp);

  return pfv;
}

// ----------------------------------------------------------------
void printTextOutput(const std::map<std::string, int>& repsWithCounts) {
  int clusterIndex = 0;
  for (const auto& repWithCount : repsWithCounts) {
    const std::string filename = repWithCount.first;
    int clusterSize = repWithCount.second;
    clusterIndex++;

    printf(
        "clidx=%d,clusz=%d,filename=%s\n",
        clusterIndex,
        clusterSize,
        filename.c_str());
  }
}
