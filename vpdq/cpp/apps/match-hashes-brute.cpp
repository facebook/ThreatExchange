// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#include <vpdq/cpp/hashing/matchTwoHash.h>
#include <vpdq/cpp/hashing/vpdqHashType.h>
#include <vpdq/cpp/io/vpdqio.h>

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

static void usage(char* argv0, int rc) {
  FILE* fp = (rc == 0) ? stdout : stderr;
  fprintf(
      fp,
      "Usage: %s [options] queryFilename targetFilename hamming_distance_tolerance quality_tolerance\n",
      argv0);
  fprintf(fp, "Options:\n");
  fprintf(fp, "-v|--verbose: Show all hash matching information\n");
  std::exit(rc);
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
    if ((std::string(argv[argi]) == "-v") ||
        (std::string(argv[argi]) == "--verbose")) {
      verbose = true;
      continue;
    }
  }

  if (argi > argc - 4) {
    usage(argv[0], 1);
  }
  distanceTolerance = std::stoi(argv[argi + 2]);
  qualityTolerance = std::stoi(argv[argi + 3]);
  std::vector<facebook::vpdq::hashing::vpdqFeature> qHashes;
  std::vector<facebook::vpdq::hashing::vpdqFeature> tHashes;
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
  facebook::vpdq::hashing::matchTwoHashBrute(
      qHashes,
      tHashes,
      distanceTolerance,
      qualityTolerance,
      qMatch,
      tMatch,
      verbose);
  // Print float with 2 decimal places
  printf("%0.2f Percentage Query Video match\n", qMatch);
  printf("%0.2f Percentage Target Video match\n", tMatch);
  return EXIT_SUCCESS;
}
