// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#include <pdq/cpp/common/pdqhashtypes.h>
#include <pdq/cpp/io/hashio.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

// ================================================================
// This is an ops tool for doing various things to 256-bit hashes
// with Hamming-distance metric.
//
// Input is 256-bit hex-formatted hashes, one per line.
//
// Please see the usage function for more information.
// ================================================================
using namespace facebook::pdq::hashing;
using namespace facebook::pdq::io;

static void usage(char* argv0, int rc);
static void do_norms(char* argv0, char* argv1, int argc, char** argv);
static void do_slot_norms(char* argv0, char* argv1, int argc, char** argv);
static void do_deltas(char* argv0, char* argv1, int argc, char** argv);
static void do_adjacent_xors(char* argv0, char* argv1, int argc, char** argv);
static void do_xors_from_first(char* argv0, char* argv1, int argc, char** argv);
static void
do_matrix(char* argv0, char* argv1, int argc, char** argv, bool do_cij);
static void
do_pairwise_distances(char* argv0, char* argv1, int argc, char** argv);
static void do_bits(char* argv0, char* argv1, int argc, char** argv);
static void do_words(char* argv0, char* argv1, int argc, char** argv);
static void do_fuzz(char* argv0, char* argv1, int argc, char** argv);

// ----------------------------------------------------------------
static void usage(char* argv0, int rc) {
  FILE* fp = (rc == 0) ? stdout : stderr;
  fprintf(fp, "Usage: %s {verb} [zero or more hash-files]\n", argv0);
  fprintf(fp, "Hashes should be in hexadecimal format without leading 0x.\n");
  fprintf(
      fp,
      "If zero filenames are given on the command line, hashes are "
      "read from stdin.\n");
  fprintf(fp, "Norms and distances are computed using Hamming distance.\n");
  fprintf(fp, "Verbs:\n");
  fprintf(
      fp,
      " norms:              Show hamming norms of hashes.\n"
      " slotnorms:          Show slotwise (16-bit) hamming norms of hashes.\n"
      " deltas:             Print hamming distances between adjacent hashes.\n"
      " axors:              Print XORs of adjacent hashes.\n"
      " fxors:              Print XORs of each hash with respect to the first.\n"
      " matrix:             Print matrix of pairwise hamming distances.\n"
      " cij:                Print DKVP-formatted pairwise-distance data.\n"
      " pairwise-distances: Compute pairwise distances given two filenames\n"
      " bits:               Format hashes as 2D binary matrices\n"
      " words:              Format hashes as space-delimited 16-bit words in "
      "hex\n"
      " fuzz {n}:           Randomly flip n bits (with replacement) in the "
      "input hashes.\n");
  exit(rc);
}

// ----------------------------------------------------------------
int main(int argc, char** argv) {
  srandom(time(nullptr) ^ getpid()); // seed the RNG for Hash256::fuzz

  // Parse command-line flags. I'm expliclily not using gflags or other such
  // libraries, to minimize the number of external dependencies for this
  // project.
  if (argc < 2) {
    usage(argv[0], 1);
  } else if (!strcmp(argv[1], "-h") || !strcmp(argv[1], "--help")) {
    usage(argv[0], 0);
  } else if (!strcmp(argv[1], "norms")) {
    do_norms(argv[0], argv[1], argc - 2, argv + 2);
  } else if (!strcmp(argv[1], "slotnorms")) {
    do_slot_norms(argv[0], argv[1], argc - 2, argv + 2);
  } else if (!strcmp(argv[1], "deltas")) {
    do_deltas(argv[0], argv[1], argc - 2, argv + 2);
  } else if (!strcmp(argv[1], "axors")) {
    do_adjacent_xors(argv[0], argv[1], argc - 2, argv + 2);
  } else if (!strcmp(argv[1], "fxors")) {
    do_xors_from_first(argv[0], argv[1], argc - 2, argv + 2);
  } else if (!strcmp(argv[1], "matrix")) {
    do_matrix(argv[0], argv[1], argc - 2, argv + 2, false);
  } else if (!strcmp(argv[1], "cij")) {
    do_matrix(argv[0], argv[1], argc - 2, argv + 2, true);
  } else if (!strcmp(argv[1], "pairwise-distances")) {
    do_pairwise_distances(argv[0], argv[1], argc - 2, argv + 2);
  } else if (!strcmp(argv[1], "bits")) {
    do_bits(argv[0], argv[1], argc - 2, argv + 2);
  } else if (!strcmp(argv[1], "words")) {
    do_words(argv[0], argv[1], argc - 2, argv + 2);
  } else if (!strcmp(argv[1], "fuzz")) {
    do_fuzz(argv[0], argv[1], argc - 2, argv + 2);

  } else {
    usage(argv[0], 1);
  }
  return 0;
}

// ----------------------------------------------------------------
static void
do_norms(char* /*unused*/, char* /*unused*/, int argc, char** argv) {
  std::vector<Hash256> hashes;
  loadHashesFromFilesOrDie(argv, argc, hashes);
  for (auto hash : hashes) {
    printf("%s %d\n", hash.format().c_str(), hash.hammingNorm());
  }
}

// ----------------------------------------------------------------
static void
do_slot_norms(char* /*unused*/, char* /*unused*/, int argc, char** argv) {
  std::vector<Hash256> hashes;
  loadHashesFromFilesOrDie(argv, argc, hashes);
  for (auto hash : hashes) {
    printf("%s", hash.format().c_str());
    for (int i = 0; i < HASH256_NUM_WORDS; i++) {
      printf(" %2d", __builtin_popcount(hash.w[i]));
    }
    printf("\n");
  }
}

// ----------------------------------------------------------------
static void
do_deltas(char* /*unused*/, char* /*unused*/, int argc, char** argv) {
  std::vector<Hash256> hashes;
  loadHashesFromFilesOrDie(argv, argc, hashes);
  for (int i = 0; i < (int)hashes.size(); i++) {
    if (i == 0) {
      printf("%s\n", hashes[i].format().c_str());
    } else {
      printf(
          "%s %d\n",
          hashes[i].format().c_str(),
          hashes[i].hammingDistance(hashes[i - 1]));
    }
  }
}

// ----------------------------------------------------------------
static void
do_adjacent_xors(char* /*unused*/, char* /*unused*/, int argc, char** argv) {
  std::vector<Hash256> hashes;
  loadHashesFromFilesOrDie(argv, argc, hashes);
  for (int i = 1; i < (int)hashes.size(); i++) {
    Hash256 x = hashes[i - 1] ^ hashes[i];
    printf("%s\n", x.format().c_str());
  }
}

// ----------------------------------------------------------------
static void
do_xors_from_first(char* /*unused*/, char* /*unused*/, int argc, char** argv) {
  std::vector<Hash256> hashes;
  loadHashesFromFilesOrDie(argv, argc, hashes);
  for (int i = 1; i < (int)hashes.size(); i++) {
    Hash256 x = hashes[0] ^ hashes[i];
    printf("%s\n", x.format().c_str());
  }
}

// ----------------------------------------------------------------
static void
do_matrix(char* argv0, char* /*unused*/, int argc, char** argv, bool do_cij) {
  std::vector<Hash256> hashes1;
  std::vector<Hash256> hashes2;

  if (argc == 0) {
    loadHashesFromStream(stdin, hashes1);
    hashes2 = hashes1;
  } else if (argc == 1) {
    loadHashesFromFile(argv[0], hashes1);
    hashes2 = hashes1;
  } else if (argc == 2) {
    loadHashesFromFile(argv[0], hashes1);
    loadHashesFromFile(argv[1], hashes2);
  } else {
    usage(argv0, 1);
    exit(1);
  }

  if (do_cij) {
    for (int i = 0; i < (int)hashes1.size(); i++) {
      for (int j = 0; j < (int)hashes2.size(); j++) {
        printf(
            "ci=%s,cj=%s,i=%d,j=%d,d=%d\n",
            hashes1[i].format().c_str(),
            hashes2[j].format().c_str(),
            i,
            j,
            hashes1[i].hammingDistance(hashes2[j]));
      }
    }
  } else {
    for (int i = 0; i < (int)hashes1.size(); i++) {
      for (int j = 0; j < (int)hashes2.size(); j++) {
        printf(" %3d", hashes1[i].hammingDistance(hashes2[j]));
      }
      printf("\n");
    }
  }
}

// ----------------------------------------------------------------
static void
do_pairwise_distances(char* argv0, char* argv1, int argc, char** argv) {
  if (argc != 2) {
    fprintf(stderr, "%s %s: need two filenames.\n", argv0, argv1);
    exit(1);
  }
  std::vector<Hash256> hashes1;
  std::vector<Hash256> hashes2;

  loadHashesFromFileOrDie(argv[0], hashes1);
  loadHashesFromFileOrDie(argv[1], hashes2);

  for (int i = 0; i < (int)hashes1.size() && i < (int)hashes2.size(); i++) {
    printf("%3d\n", hashes1[i].hammingDistance(hashes2[i]));
  }
}

// ----------------------------------------------------------------
static void do_bits(char* /*unused*/, char* /*unused*/, int argc, char** argv) {
  std::vector<Hash256> hashes;
  loadHashesFromFilesOrDie(argv, argc, hashes);
  for (auto hash : hashes) {
    hash.dumpBits();
  }
}

// ----------------------------------------------------------------
static void
do_words(char* /*unused*/, char* /*unused*/, int argc, char** argv) {
  std::vector<Hash256> hashes;
  loadHashesFromFilesOrDie(argv, argc, hashes);
  for (auto hash : hashes) {
    hash.dumpWords();
  }
}

// ----------------------------------------------------------------
static void do_fuzz(char* argv0, char* argv1, int argc, char** argv) {
  int numErrorBits = 0;
  if (argc < 1) {
    fprintf(stderr, "%s %s: need number of bits to fuzz.\n", argv0, argv1);
    exit(1);
  }
  if (sscanf(argv[0], "%d", &numErrorBits) != 1) {
    fprintf(
        stderr,
        "%s %s: couldn't scan \"%s\" as number of bits to fuzz.\n",
        argv0,
        argv1,
        argv[0]);
    exit(1);
  }
  argc--;
  argv++;

  std::vector<Hash256> hashes;
  loadHashesFromFilesOrDie(argv, argc, hashes);
  for (auto hash : hashes) {
    hash = hash.fuzz(numErrorBits);
    printf("%s\n", hash.format().c_str());
  }
}
