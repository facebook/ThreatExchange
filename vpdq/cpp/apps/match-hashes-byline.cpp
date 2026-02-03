// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#include <pdq/cpp/io/hashio.h>
#include <vpdq/cpp/hashing/vpdqHashType.h>
#include <vpdq/cpp/io/vpdqio.h>

#include <cstdlib>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <string>

static void usage(char* argv0, int rc) {
  FILE* fp = (rc == 0) ? stdout : stderr;
  fprintf(
      fp,
      "Usage: %s [options] file1name file2name hamming_distanceTolerance qualityTolerance\n",
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

  std::vector<facebook::vpdq::hashing::vpdqFeature> video1Hashes;
  std::vector<facebook::vpdq::hashing::vpdqFeature> video2Hashes;
  bool ret =
      facebook::vpdq::io::loadHashesFromFileOrDie(argv[argi], video1Hashes);
  if (!ret) {
    return EXIT_FAILURE;
  }
  ret =
      facebook::vpdq::io::loadHashesFromFileOrDie(argv[argi + 1], video2Hashes);
  if (!ret) {
    return EXIT_FAILURE;
  }

  distanceTolerance = std::stoi(argv[argi + 2]);
  qualityTolerance = std::stoi(argv[argi + 3]);

  if (video1Hashes.size() != video2Hashes.size()) {
    std::cerr << "VideoHashes1 size " << video1Hashes.size()
              << " doesn't match with VideoHashes2 size " << video2Hashes.size()
              << std::endl;
    return EXIT_FAILURE;
  }
  size_t count = 0;
  size_t total_hashed_compared = 0;
  for (size_t i = 0; i < video1Hashes.size(); i++) {
    if (video1Hashes[i].quality < qualityTolerance ||
        video2Hashes[i].quality < qualityTolerance) {
      if (verbose) {
        std::cout << "Skipping Line " << i
                  << " Hash1: " << video1Hashes[i].pdqHash.format()
                  << " Hash2: " << video2Hashes[i].pdqHash.format()
                  << ", because of low quality Hash1: "
                  << video1Hashes[i].quality
                  << " Hash2: " << video2Hashes[i].quality << std::endl;
      }
      continue;
    }
    total_hashed_compared++;
    if (video1Hashes[i].pdqHash.hammingDistance(video2Hashes[i].pdqHash) <
        distanceTolerance) {
      count++;
      if (verbose) {
        std::cout << "Line " << i
                  << " Hash1: " << video1Hashes[i].pdqHash.format()
                  << " Hash2: " << video2Hashes[i].pdqHash.format() << " match"
                  << std::endl;
      }
    } else {
      if (verbose) {
        std::cout << "NO MATCH: Line " << i
                  << " Hash1: " << video1Hashes[i].pdqHash.format()
                  << " Hash2: " << video2Hashes[i].pdqHash.format()
                  << std::endl;
      }
    }
  }

  auto const percentage =
      static_cast<float>(count) * 100 / total_hashed_compared;
  std::cout << std::fixed << std::setprecision(3) << percentage
            << " Percentage matches" << std::endl;
  return EXIT_SUCCESS;
}
