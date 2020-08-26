// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

// ================================================================
// This is a naive technique for finding clusters of videos having pairwise
// cosine similarity over a given threshold, e.g. 0.98 (where 1.0 is a perfect
// match).
//
// It uses no indexing so it requires O(N^2) cosine-similarity computations
// between each video-pairs' coarse features.  Nonetheless it runs on over 1000
// feature-vector files in just a few seconds.
//
// It's a quick-peek way to look for similar videos within a collection.
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

int handleInputFp(
    const char* argv0,
    const char* tmkFileName,
    FILE* inputFp,
    std::map<std::string, std::shared_ptr<TMKFeatureVectors>>&
        metadataToFeatures);

void snowballClusterize(
    const std::map<std::string, std::shared_ptr<TMKFeatureVectors>>
        metadataToFeatures,
    float c1,
    float c2,
    bool level1Only,
    std::map<std::string, std::set<std::string>>& equivalenceClasses,
    char* argv0);

void printTextOutput(
    const std::map<std::string, std::set<std::string>>& equivalenceClasses,
    int minClusterSizeToPrint,
    bool printSeparateClusters);

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
  fprintf(fp, "-s:         Print a blank line between similarity clusters.\n");
  fprintf(
      fp,
      "--c1 {x}: Level-1 threshold: default %.3f.\n",
      DEFAULT_LEVEL_1_THRESHOLD);
  fprintf(
      fp,
      "--c2 {y}: Level-2 threshold: default %.3f.\n",
      DEFAULT_LEVEL_2_THRESHOLD);
  fprintf(fp, "--level-1-only: Don't do level-2 thresholding (runs faster).\n");
  fprintf(fp, "--min {n}:  Only print clusters of size n or more. Using 2\n");
  fprintf(fp, "            suppresses output of singletons.\n");
  exit(exit_rc);
}

// ================================================================
int main(int argc, char** argv) {
  bool fileNamesFromStdin = false;
  bool printSeparateClusters = false;
  float c1 = DEFAULT_LEVEL_1_THRESHOLD;
  float c2 = DEFAULT_LEVEL_2_THRESHOLD;
  bool level1Only = false;
  int minClusterSizeToPrint = 1;

  int argi = 1;
  while ((argi < argc) && argv[argi][0] == '-') {
    char* flag = argv[argi++];
    if (!strcmp(flag, "-h") || !strcmp(flag, "--help")) {
      usage(argv[0], 0);

    } else if (!strcmp(flag, "-i")) {
      fileNamesFromStdin = true;
    } else if (!strcmp(flag, "-s")) {
      printSeparateClusters = true;

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

    } else if (!strcmp(flag, "--min")) {
      if (argi >= argc) {
        usage(argv[0], 1);
      }
      if (sscanf(argv[argi], "%d", &minClusterSizeToPrint) != 1) {
        usage(argv[0], 1);
      }
      argi++;

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

  // INGEST FEATURES
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

  // CLUSTERIZE
  std::map<std::string, std::set<std::string>> equivalenceClasses;
  snowballClusterize(
      metadataToFeatures, c1, c2, level1Only, equivalenceClasses, argv[0]);

  // PRINT OUTPUT
  printTextOutput(
      equivalenceClasses, minClusterSizeToPrint, printSeparateClusters);

  return 0;
}

// ----------------------------------------------------------------
void handleInputFileNameOrDie(
    const char* argv0,
    const char* tmkFileName,
    std::map<std::string, std::shared_ptr<TMKFeatureVectors>>&
        metadataToFeatures) {
  FILE* inputFp =
      facebook::tmk::io::openFileOrDie(tmkFileName, (char*)"rb", argv0);
  handleInputFp(argv0, tmkFileName, inputFp, metadataToFeatures);
  fclose(inputFp);
}

// ----------------------------------------------------------------
int handleInputFp(
    const char* argv0,
    const char* tmkFileName,
    FILE* inputFp,
    std::map<std::string, std::shared_ptr<TMKFeatureVectors>>&
        metadataToFeatures) {
  std::shared_ptr<TMKFeatureVectors> pfv =
      TMKFeatureVectors::readFromInputStream(inputFp, argv0);

  if (pfv == nullptr) {
    fprintf(stderr, "%s: failed to read \"%s\".\n", argv0, tmkFileName);
    // error message already printed out?
    exit(1);
  }

  metadataToFeatures[std::string(tmkFileName)] = pfv;

  return 0;
}

// ----------------------------------------------------------------
void snowballClusterize(
    const std::map<std::string, std::shared_ptr<TMKFeatureVectors>>
        metadataToFeatures,
    float c1,
    float c2,
    bool level1Only,
    std::map<std::string, std::set<std::string>>& equivalenceClasses,
    char* argv0) {
  std::map<std::string, std::set<std::string>> adjacencyMatrix;

  // COMPUTE THE ADJACENCY MATRIX
  for (const auto& it1 : metadataToFeatures) {
    const std::string& filename1 = it1.first;
    const std::shared_ptr<TMKFeatureVectors> pfv1 = it1.second;
    // printf("... %s\n", filename1.c_str());
    for (const auto& it2 : metadataToFeatures) {
      const std::string& filename2 = it2.first;
      const std::shared_ptr<TMKFeatureVectors> pfv2 = it2.second;
      // The adjacency matrix is symmetric. So write both sides of the
      // diagonal, but do the math only one per pair.
      if (filename1 <= filename2) {
        if (!TMKFeatureVectors::areCompatible(*pfv1, *pfv2)) {
          fprintf(
              stderr,
              "%s: immiscible provenances:\n%s\n%s\n",
              argv0,
              filename1.c_str(),
              filename2.c_str());
          exit(1);
        }
        float s1 = TMKFeatureVectors::computeLevel1Score(*pfv1, *pfv2);
        if (s1 >= c1) {
          if (level1Only) {
            adjacencyMatrix[filename1].insert(filename2);
            adjacencyMatrix[filename2].insert(filename1);
          } else {
            float s2 = TMKFeatureVectors::computeLevel2Score(*pfv1, *pfv2);
            if (s2 >= c2) {
              adjacencyMatrix[filename1].insert(filename2);
              adjacencyMatrix[filename2].insert(filename1);
            }
          }
        }
      }
    }
  }

  // IDENTIFY CLUSTER REPRESENTATIVES

  // For the sake of discussion suppose the item IDs are A, B, C, D, E.
  // Input data includes the adjacency matrix
  //
  //     A B C D E
  //   A * . * * .
  //   B . * . * .
  //   C * . * . .
  //   D * * . * .
  //   E . . . . *
  //
  // We expect to get [A,B,C,D] as one equivalence class and [E] as the other.
  // Representatives are just the first-found, e.g. A and E respectively.

  std::map<std::string, std::string> metadatasToClusterRepresentatives;

  // For each row of the adjacency matrix:
  for (const auto& row_it : adjacencyMatrix) {
    const std::string& metadata_i = row_it.first;
    const std::set<std::string>& metadata_js = row_it.second;

    // Already-visited items, found by off-diagonal on a previous row
    if (metadatasToClusterRepresentatives.find(metadata_i) !=
        metadatasToClusterRepresentatives.end()) {
      continue;
    }

    // Each row of the adjacency matrix contributes to an equivalence class.
    // E.g. the top row of the above example gives [A,C,D]. The only question
    // is whether this is standalone or part of something already seen. For
    // example, on the first row we get [A,C,D]. On the second row we have
    // [B,D] but D was already seen.

    // Find a representative for this item: Either the first-found in the
    // row, or an already-seen (if there is one).
    std::string representative = metadata_i; // E.g. A on 1st row, B on 2nd row
    for (const std::string& metadata_j : metadata_js) {
      if (metadatasToClusterRepresentatives.find(metadata_j) !=
          metadatasToClusterRepresentatives.end()) {
        representative = metadatasToClusterRepresentatives[metadata_j];
        break;
      }
    }

    // Mark all the items in the current row as having that representative
    for (const std::string& metadata_j : metadata_js) {
      metadatasToClusterRepresentatives[metadata_j] = representative;
    }
  }

  // FORM EQUIVALENCE CLASSES
  for (const auto& it : metadataToFeatures) {
    const std::string& metadata = it.first;
    std::string& representative = metadatasToClusterRepresentatives[metadata];
    equivalenceClasses[representative].insert(metadata);
  }
}

// ----------------------------------------------------------------
void printTextOutput(
    const std::map<std::string, std::set<std::string>>& equivalenceClasses,
    int minClusterSizeToPrint,
    bool printSeparateClusters) {
  int clusterIndex = 0;
  for (const auto& it : equivalenceClasses) {
    const std::set<std::string>& equivalenceClass = it.second;
    int clusterSize = equivalenceClass.size();
    if (clusterSize < minClusterSizeToPrint) {
      continue;
    }
    clusterIndex++;

    if (printSeparateClusters && clusterIndex > 1) {
      printf("\n");
    }

    for (const std::string& filename : equivalenceClass) {
      printf(
          "clidx=%d,clusz=%d,filename=%s\n",
          clusterIndex,
          clusterSize,
          filename.c_str());
    }
  }
}
