// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#include <cstdlib>
#include <cstring>

#include <pdq/cpp/io/hashio.h>
#include <vpdq/cpp/hashing/matchTwoHash.h>
#include <vpdq/cpp/hashing/vpdqHashType.h>
#include <vpdq/cpp/io/vpdqio.h>

using namespace std;
using namespace facebook;

static void usage(char* argv0, int rc) {
  FILE* fp = (rc == 0) ? stdout : stderr;
  fprintf(
      fp,
      "Usage: %s [options] queryFilename targetFilename hamming_distance_tolerance quality_tolerance\n",
      argv0);
  fprintf(fp, "Options:\n");
  fprintf(fp, "-v|--verbose: Show all hash matching information\n");
  exit(rc);
}

int main(int argc, char** argv) {
  int argi = 1;
  bool verbose = false;
  int distanceTolerance = 0;
  int qualityTolerance = 0;

  for (; argi < argc; argi++) {
    if (argv[argi][0] != '-') {
      break;
    }
    if (!strcmp(argv[argi], "-v") || !strcmp(argv[argi], "--verbose")) {
      verbose = true;
      continue;
    }
  }

  if (argi > argc - 4) {
    usage(argv[0], 1);
  }
  distanceTolerance = atoi(argv[argi + 2]);
  qualityTolerance = atoi(argv[argi + 3]);
  vector<facebook::vpdq::hashing::vpdqFeature> qHashes;
  vector<facebook::vpdq::hashing::vpdqFeature> tHashes;
  bool ret = facebook::vpdq::io::loadHashesFromFileOrDie(argv[argi], qHashes);
  if (!ret) {
    return EXIT_FAILURE;
  }
  ret = facebook::vpdq::io::loadHashesFromFileOrDie(argv[argi + 1], tHashes);
  if (!ret) {
    return EXIT_FAILURE;
  }
  double qMatch = 0;
  double tMatch = 0;
  ret = facebook::vpdq::hashing::matchTwoHashBrute(
      qHashes,
      tHashes,
      distanceTolerance,
      qualityTolerance,
      qMatch,
      tMatch,
      verbose);
  if (!ret) {
    return EXIT_FAILURE;
  }
  // Print float with 2 decimal places
  printf("%0.2f Percentage Query Video match\n", qMatch);
  printf("%0.2f Percentage Target Video match\n", tMatch);
  return EXIT_SUCCESS;
}
