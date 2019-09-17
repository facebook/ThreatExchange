// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#include <pdq/cpp/io/hashio.h>
#include <pdq/cpp/index/mih.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <set>
#include <chrono>

// ================================================================
// For regression-test usage. See also mih-query.cpp.
// ================================================================

static void usage(char* argv0, int rc);
static void do_test_1(char* argv0, int argc, char** argv);
static void do_test_2(char* argv0, int argc, char** argv);

// ----------------------------------------------------------------
int main(int argc, char** argv) {
  // Parse command-line flags. I'm explicitly not using gflags or other such
  // libraries, to minimize the number of external dependencies for this
  // project.
  if (argc < 2)
    usage(argv[0], 1);
  if (!strcmp(argv[1], "-h") || !strcmp(argv[1], "--help")) {
    usage(argv[0], 0);
  } else if (!strcmp(argv[1], "test1")) {
    do_test_1(argv[0], argc-2, argv+2);
  } else if (!strcmp(argv[1], "test2")) {
    do_test_2(argv[0], argc-2, argv+2);

  } else {
    usage(argv[0], 1);
  }
  return 0;
}

// ----------------------------------------------------------------
static void usage(char* argv0, int rc) {
  FILE* fp = (rc == 0) ? stdout : stderr;
  fprintf(fp, "Usage: %s {test1} [zero or more hashes]\n", argv0);
  fprintf(fp, "Hashes should be in hexadecimal format without leading 0x.\n");
  fprintf(fp, "If zero hashes are given on the command line, they are "
    "read from stdin.\n");
  exit(rc);
}

// ----------------------------------------------------------------
// This is for regression-test use, to test the lazily-filled
// nearest-neighbors cache on 16-bit words within MIH256.

static void do_test_1(char* argv0, int argc, char** argv) {
  int d = 32;
  int idx = 0;
  facebook::pdq::hashing::Hash256 h, n;
  facebook::pdq::index::MIH256<int> mih;
  std::vector<std::pair<facebook::pdq::hashing::Hash256,int>> matches;

  h.clear();
  h.setBit(0);
  h.setBit(2);
  h.setBit(7);
  h.setBit(9);
  mih.insert(h, idx++);

  h.clear();
  h.setBit(1);
  h.setBit(2);
  h.setBit(7);
  h.setBit(9);
  mih.insert(h, idx++);

  h.clear();
  h.setBit(0);
  h.setBit(3);
  h.setBit(6);
  h.setBit(7);
  h.setBit(9);
  mih.insert(h, idx++);

  mih.dump();

  n.clear();
  n.setBit(0);
  n.setBit(3);
  n.setBit(6);
  n.setBit(8);
  n.setBit(9);

  mih.queryAll(n, d, matches);
}

// ----------------------------------------------------------------
static void test_2_usage(char* argv0) {
  fprintf(stderr, "Usage: %s test2 [-v] [--no-timings] {d} {needles} {haystack}\n",
    argv0);
  exit(1);
}

static void do_test_2(char* argv0, int argc, char** argv) {
  int maxDistance = 32;
  facebook::pdq::hashing::Hash256 needle;
  std::vector<std::pair<facebook::pdq::hashing::Hash256,std::string>> needles;
  std::vector<std::pair<facebook::pdq::hashing::Hash256,std::string>> haystack;
  bool verbose = false;
  bool do_timings = true; // Omit for regtest so we can use exact diff

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Parse the command line
  while (argc > 0 && argv[0][0] == '-') {
    if (!strcmp(argv[0], "-v")) {
      verbose = true;
    } else if (!strcmp(argv[0], "--no-timings")) {
      do_timings = false;
    } else {
      test_2_usage(argv0);
    }
    argc--;
    argv++;
  }

  if (argc != 3) {
    test_2_usage(argv0);
  }
  (void)sscanf(argv[0], "%d", &maxDistance);
  char* needles_filename = argv[1];
  char* haystack_filename = argv[2];

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Load input data
  if (! facebook::pdq::io::loadHashesAndMetadataFromFile(needles_filename, needles)) {
    exit(1); // error message already printed out
  }
  if (! facebook::pdq::io::loadHashesAndMetadataFromFile(haystack_filename, haystack)) {
    exit(1); // error message already printed out
  }

  if (verbose) {
    printf("NEEDLES:\n");
    for (auto it : needles) {
      facebook::pdq::hashing::Hash256 hash = it.first;
      std::string metadata = it.second;
      printf("%s,%s\n", hash.format().c_str(), metadata.c_str());
    }
    printf("\n");

    printf("ORIGINAL HAYSTACK:\n");
    for (auto it : haystack) {
      facebook::pdq::hashing::Hash256 hash = it.first;
      std::string metadata = it.second;
      printf("%s,%s\n", hash.format().c_str(), metadata.c_str());
    }
    printf("\n");
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Build the MIH
  std::vector<std::pair<facebook::pdq::hashing::Hash256,std::string>> matches;
  int num_matches = 0;

  std::chrono::time_point<std::chrono::system_clock> t1, t2;
  std::chrono::duration<double> elapsed_seconds_outer;
  double seconds;

  facebook::pdq::index::MIH256<std::string> mih;

  t1 = std::chrono::system_clock::now();
  for (auto it : haystack) {
    facebook::pdq::hashing::Hash256 hash = it.first;
    std::string metadata = it.second;
    mih.insert(hash, metadata);
  }
  t2 = std::chrono::system_clock::now();
  elapsed_seconds_outer = t2 - t1;
  seconds = elapsed_seconds_outer.count();
  if (do_timings) {
    printf("MIH BUILD SECONDS:          %.6lf\n", seconds);
  }
  printf("\n");
  if (verbose) {
    printf("\n");
    mih.dump();
    printf("\n");
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Do linear searches
  matches.clear();
  num_matches = 0;

  t1 = std::chrono::system_clock::now();
  for (auto it : needles) {
    facebook::pdq::hashing::Hash256 needle = it.first;
    mih.bruteForceQueryAll(needle, maxDistance, matches);
    num_matches += matches.size();
    if (verbose) {
      printf("BRUTE-FORCE MATCHES:\n");
      for (auto it : matches) {
        facebook::pdq::hashing::Hash256 hash = it.first;
        std::string metadata = it.second;
        printf("%s,%s\n", hash.format().c_str(), metadata.c_str());
      }
    }
  }
  t2 = std::chrono::system_clock::now();
  elapsed_seconds_outer = t2 - t1;
  seconds = elapsed_seconds_outer.count();

  printf("BRUTE-FORCE QUERY:\n");
  printf("NEEDLE COUNT:               %d\n", (int)needles.size());
  printf("HAYSTACK COUNT:             %d\n", (int)mih.size());
  printf("TOTAL MATCH COUNT:          %d\n", (int)num_matches);
  if (do_timings) {
    printf("SECONDS:                    %.6lf\n", seconds);
    printf("SECONDS PER NEEDLE:         %.6lf\n", seconds / needles.size());
    printf("SECONDS PER MATCH:          %.6lf\n", seconds / num_matches);
  }
  printf("\n");

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Do indexed searches
  matches.clear();
  num_matches = 0;

  t1 = std::chrono::system_clock::now();
  for (auto it : needles) {
    facebook::pdq::hashing::Hash256 needle = it.first;
    mih.queryAll(needle, maxDistance, matches);
    num_matches += matches.size();
    if (verbose) {
      printf("PRUNED MATCHES:\n");
      for (auto it : matches) {
        facebook::pdq::hashing::Hash256 hash = it.first;
        std::string metadata = it.second;
        printf("%s,%s\n", hash.format().c_str(), metadata.c_str());
      }
    }
  }
  t2 = std::chrono::system_clock::now();
  elapsed_seconds_outer = t2 - t1;
  seconds = elapsed_seconds_outer.count();

  printf("MIH QUERY:\n");
  printf("NEEDLE COUNT:               %d\n", (int)needles.size());
  printf("HAYSTACK COUNT:             %d\n", (int)mih.size());
  printf("TOTAL MATCH COUNT:          %d\n", (int)num_matches);
  if (do_timings) {
    printf("SECONDS:                    %.6lf\n", seconds);
    printf("SECONDS PER NEEDLE:         %.6lf\n", seconds / needles.size());
    printf("SECONDS PER MATCH:          %.6lf\n", seconds / num_matches);
  }
  printf("\n");
}
