// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

// ================================================================
// Given a pair of `.tmk` files (see section below on file formats), uses
// tmk compare tmks to see if the .tmk files are the same to a certain
// relative error.
//
// This sees if two `.tmk` files are the same, within roundoff error anyway.
// This is **not** intended for video-matching between potential variations of
// a video -- see `tmk-query` for that. Rather, this program is intended for
// comparing hashes of the **exact same video**, for regression or portability
// concerns.
// ================================================================

#include <tmk/cpp/algo/tmkfv.h>
#include <tmk/cpp/lib/vec.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

using namespace facebook::tmk;
using namespace facebook::tmk::algo;

// ================================================================
void usage(const char* argv0, int exit_rc) {
  FILE* fp = (exit_rc == 0) ? stdout : stderr;
  fprintf(
      fp, "Usage: %s [options] {tmk file name 1} {tmk file name 2}\n", argv0);
  fprintf(fp, "Options:\n");
  fprintf(fp, "-s|--strict Use cosine and sine equality.\n");
  fprintf(fp, "-v|--verbose Print intermediate info for debugging.\n");
  exit(exit_rc);
}

// ================================================================
int main(int argc, char** argv) {
  bool strict = false;
  bool verbose = false;
  int argi = 1;

  while ((argi < argc) && argv[argi][0] == '-') {
    char* flag = argv[argi++];
    if (!strcmp(flag, "-h") || !strcmp(flag, "--help")) {
      usage(argv[0], 0);
    } else if (!strcmp(flag, "-s") || !strcmp(flag, "--strict")){
      strict = true;
    } else if (!strcmp(flag, "-v") || !strcmp(flag, "--verbose")){
      verbose = true;
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
  float tol = 0.08;
  bool ok;
  float minScore = 1.0 - tol; // Perfect matches will have level 1 and 2 scores of 1.0

  if (strict){
    ok = TMKFeatureVectors::compare(*pfva, *pfvb, tol);
    if(verbose){
      fprintf(stderr, "Using sine and cosine similarity.\n");
    }
  } else {
    float score1 = TMKFeatureVectors::computeLevel1Score(*pfva, *pfvb) > minScore;
    float score2 = TMKFeatureVectors::computeLevel2Score(*pfva, *pfvb)  > minScore;
    ok = (score1 > minScore) && (score2 > minScore);
    if(verbose){
      fprintf(stderr, "Level 1 Score: %f Level 2 Score: %f Tolerance: %f\n", score1, score2, tol);
    }
  }

  if (!ok) {
    fprintf(
        stderr,
        "TMK files do not match:\n%s\n%s\n",
        tmkFileNameA,
        tmkFileNameB);
    exit(1);
  } else {
    fprintf(
        stderr,
        "TMK files match:\n%s\n%s\n",
        tmkFileNameA,
        tmkFileNameB);
    exit(0);
  }
}
