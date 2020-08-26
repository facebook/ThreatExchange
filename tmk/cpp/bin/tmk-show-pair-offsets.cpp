// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

// ================================================================
// Given a pair of `.tmk` files (see section below on file formats), computes
// the cosine-similarity score of their time-average 'coarse' features, and the
// optimal detected time-shift (modulo periods) between the two videos.
// ================================================================

#include <tmk/cpp/algo/tmkfv.h>
#include <tmk/cpp/lib/vec.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

using namespace facebook::tmk;
using namespace facebook::tmk::algo;

// ================================================================
void usage(char* argv0, int exit_rc) {
  FILE* fp = (exit_rc == 0) ? stdout : stderr;
  fprintf(
      fp, "Usage: %s [options] {TMK file name 1} {TMK file name 2}\n", argv0);
  fprintf(fp, "Options:\n");
  fprintf(fp, "-v|--verbose Print details of K-delta results.\n");
  exit(exit_rc);
}

// ================================================================
int main(int argc, char** argv) {
  bool printDetails = false;
  int argi = 1;
  while ((argi < argc) && argv[argi][0] == '-') {
    char* flag = argv[argi++];
    if (!strcmp(flag, "-h") || !strcmp(flag, "--help")) {
      usage(argv[0], 0);
    } else if (!strcmp(flag, "-v") || !strcmp(flag, "--verbose")) {
      printDetails = true;
    } else {
      usage(argv[0], 1);
    }
  }

  if ((argc - argi) != 2) {
    usage(argv[0], 1);
  }
  char* tmkFileNameA = argv[argi];
  char* tmkFileNameB = argv[argi + 1];

  std::shared_ptr<TMKFeatureVectors> pfva =
      TMKFeatureVectors::readFromInputFile(tmkFileNameA, argv[0]);
  std::shared_ptr<TMKFeatureVectors> pfvb =
      TMKFeatureVectors::readFromInputFile(tmkFileNameB, argv[0]);
  if (pfva == nullptr || pfvb == nullptr) { // error message already printed out
    exit(1);
  }

  if (!TMKFeatureVectors::areCompatible(*pfva, *pfvb)) {
    fprintf(
        stderr,
        "%s: immiscible provenances:\n%s\n%s\n",
        argv[0],
        tmkFileNameA,
        tmkFileNameB);
    exit(1);
  }

  float cosSim = facebook::tmk::libvec::computeCosSim(
      pfva->getPureAverageFeature(), pfvb->getPureAverageFeature());

  printf("%.6f\n", cosSim);
  facebook::tmk::algo::Periods periods = pfva->getPeriods();
  facebook::tmk::algo::BestOffsets bestOffsets;
  facebook::tmk::algo::ValuesAtBestOffsets valuesAtBestOffsets;
  TMKFeatureVectors::findPairOffsetsModuloPeriods(
      *pfva, *pfvb, bestOffsets, valuesAtBestOffsets, printDetails);
  for (int i = 0; i < periods.size(); i++) {
    // Here, unscaled to [0,1]
    printf(
        "%d mod %d: %.6f\n",
        bestOffsets[i],
        periods[i],
        valuesAtBestOffsets[i]);
  }

  return 0;
}
