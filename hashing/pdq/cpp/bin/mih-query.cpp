// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#include <pdq/cpp/index/mih.h>
#include <pdq/cpp/io/hashio.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <set>

// ================================================================
// Takes two files containing hashes with metadata: the 'needles' file and the
// 'haystack' file, and looks up each of the former within the latter.  This is
// an ops tool, as well as demo code for the PDQ reference implementation.
//
// See hashio.h for file-format information.
//
// See also the usage function for usage information.
// ================================================================

const int DEFAULT_PDQ_DISTANCE_THRESHOLD = 32;

// ----------------------------------------------------------------
static void usage(char* argv0, int rc) {
  FILE* fp = (rc == 0) ? stdout : stderr;
  fprintf(fp, "Usage: %s  [options] {needles file} {haystack file}\n", argv0);
  fprintf(fp, "Files should have one hex-formatted 256-bit hash per line,\n");
  fprintf(fp, "optionally prefixed by \"hash=\". If a comma and other text\n");
  fprintf(fp, "follows the hash, it is used as metadata; else, a counter is\n");
  fprintf(fp, "used as the metadata.\n");
  fprintf(fp, "\n");
  fprintf(fp, "Options:\n");
  fprintf(fp, "-h|--help    Print this message.\n");
  fprintf(
      fp,
      "-d {n}       Distance threshold: default %d.\n",
      DEFAULT_PDQ_DISTANCE_THRESHOLD);
  fprintf(fp, "-b|--brute-force-qeury Use linear search not MIH.\n");
  exit(rc);
}

// ----------------------------------------------------------------
int main(int argc, char** argv) {
  int doBruteForceQuery = false;
  int distanceThreshold = DEFAULT_PDQ_DISTANCE_THRESHOLD;

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Parse command-line flags. I'm expliclily not using gflags or other such
  // libraries, to minimize the number of external dependencies for this
  // project.
  int argi = 1;
  while (argi < argc) {
    if (argv[argi][0] != '-') {
      break;
    } else if (!strcmp(argv[argi], "-h") || !strcmp(argv[argi], "--help")) {
      usage(argv[0], 0);
    } else if (!strcmp(argv[argi], "-b")) {
      doBruteForceQuery = true;
      argi++;
    } else if (!strcmp(argv[argi], "--brute-force-query")) {
      doBruteForceQuery = true;
      argi++;
    } else if (!strcmp(argv[argi], "-d")) {
      if ((argc - argi) < 2) {
        usage(argv[0], 1);
      }
      if (sscanf(argv[argi + 1], "%d", &distanceThreshold) != 1) {
        usage(argv[0], 1);
      }
      argi += 2;

    } else {
      usage(argv[0], 1);
    }
  }
  if ((argc - argi) != 2) {
    usage(argv[0], 1);
  }
  char* needles_filename = argv[argi];
  char* haystack_filename = argv[argi + 1];

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Load hashes+metadata.

  facebook::pdq::hashing::Hash256 needle;
  std::vector<std::pair<facebook::pdq::hashing::Hash256, std::string>> needles;
  std::vector<std::pair<facebook::pdq::hashing::Hash256, std::string>> haystack;

  if (!facebook::pdq::io::loadHashesAndMetadataFromFile(
          needles_filename, needles)) {
    exit(1); // error message already printed out
  }
  if (!facebook::pdq::io::loadHashesAndMetadataFromFile(
          haystack_filename, haystack)) {
    exit(1); // error message already printed out
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Build the MIH data structure.

  facebook::pdq::index::MIH256<std::string> mih;
  std::vector<std::pair<facebook::pdq::hashing::Hash256, std::string>> matches;

  for (auto it : haystack) {
    facebook::pdq::hashing::Hash256 hash = it.first;
    std::string metadata = it.second;
    mih.insert(hash, metadata);
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Do the lookups.

  bool first = true;
  for (auto itn : needles) {
    needle = itn.first;

    if (!first) {
      printf("\n");
    }
    first = false;
    printf("needle=%s\n", needle.format().c_str());

    matches.clear();

    if (doBruteForceQuery) {
      mih.bruteForceQueryAll(needle, distanceThreshold, matches);
    } else {
      mih.queryAll(needle, distanceThreshold, matches);
    }
    for (auto itm : matches) {
      facebook::pdq::hashing::Hash256 hash = itm.first;
      std::string metadata = itm.second;
      printf(
          "d=%d,match=%s,%s\n",
          hash.hammingDistance(needle),
          hash.format().c_str(),
          metadata.c_str());
    }
  }

  return 0;
}
