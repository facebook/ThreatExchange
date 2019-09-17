// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

// ================================================================
// Computes the mean framewise feature for all videos in a dataset.
// Intended for parameter-tuning applications.
// ================================================================

#include <tmk/cpp/algo/tmkfv.h>
#include <tmk/cpp/io/tmkio.h>
#include <tmk/cpp/io/tmkiotypes.h>

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
  fprintf(fp, "-i: Take feature-vector-file names from stdin, not argv.\n");
  exit(exit_rc);
}

// ================================================================
int main(int argc, char** argv) {
  bool fileNamesFromStdin = false;

  int argi = 1;
  while ((argi < argc) && argv[argi][0] == '-') {
    char* flag = argv[argi++];
    if (!strcmp(flag, "-h") || !strcmp(flag, "--help")) {
      usage(argv[0], 0);

    } else if (!strcmp(flag, "-i")) {
      fileNamesFromStdin = true;

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

  if (metadataToFeatures.size() < 1) {
    fprintf(stderr, "%s: No .tmk files read.\n", argv[0]);
    exit(1);
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // ACCUMULATE MEANS
  // We can to compute the slotwise average of frame-feature vectors over all
  // videos. Meanwhile each .tmk file already has a pure-average frame
  // feature. So we simply average *those*, weighted of course by each .tmk
  // file's frame-feature count.
  std::map<io::TMKFramewiseAlgorithm, int> tmkCountsByAlgo;
  std::map<io::TMKFramewiseAlgorithm, int> frameFeatureCountsByAlgo;
  std::map<io::TMKFramewiseAlgorithm, algo::FrameFeature> sumsByAlgo;

  for (const auto& it : metadataToFeatures) {
    std::shared_ptr<TMKFeatureVectors> pfv = it.second;
    io::TMKFramewiseAlgorithm algorithm = pfv->getAlgorithm();
    int frameFeatureCount = pfv->getFrameFeatureCount();
    const algo::FrameFeature pureAverageFeature = pfv->getPureAverageFeature();

    // Guard against old .tmk files from before D8262976
    if (frameFeatureCount == 0) {
      fprintf(
          stderr,
          "%s: skipping zero frame-feature count in \"%s\".\n",
          argv[0],
          it.first.c_str());
      continue;
    }

    if (tmkCountsByAlgo.find(algorithm) == tmkCountsByAlgo.end()) {
      tmkCountsByAlgo.emplace(algorithm, 1);
    } else {
      tmkCountsByAlgo[algorithm]++;
    }

    if (frameFeatureCountsByAlgo.find(algorithm) ==
        frameFeatureCountsByAlgo.end()) {
      frameFeatureCountsByAlgo.emplace(algorithm, frameFeatureCount);
    } else {
      frameFeatureCountsByAlgo[algorithm] += frameFeatureCount;
    }

    if (sumsByAlgo.find(algorithm) == sumsByAlgo.end()) {
      sumsByAlgo.emplace(algorithm, pureAverageFeature);
    } else {
      FrameFeature& accumulator = sumsByAlgo[algorithm];
      for (int i = 0; i < pureAverageFeature.size(); i++) {
        accumulator[i] += pureAverageFeature[i] * frameFeatureCount;
      }
    }
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // DISPLAY OUTPUT
  for (const auto& it : tmkCountsByAlgo) {
    io::TMKFramewiseAlgorithm algorithm = it.first;
    int tmkCount = it.second;
    int frameFeatureCount = frameFeatureCountsByAlgo[algorithm];

    FrameFeature& accumulator = sumsByAlgo[algorithm];
    for (int i = 0; i < accumulator.size(); i++) {
      accumulator[i] /= frameFeatureCount;
    }

    printf("\n");
    printf(
        "algo=%s ntmk=%d nframe=%d featlen=%d\n",
        io::algorithmToName(algorithm).c_str(),
        tmkCount,
        frameFeatureCount,
        (int)accumulator.size());

    for (int i = 0; i < accumulator.size(); i++) {
      if (i > 0) {
        printf(" ");
      }
      printf("%.6e", accumulator[i]);
    }
    printf("\n");
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
