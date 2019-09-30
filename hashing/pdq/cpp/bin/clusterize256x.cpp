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

// ================================================================
// Takes hashes with metadata and clusters them among one another.  This is an
// ops tool, as well as demo code for the PDQ reference implementation.
//
// NOTE: There are clusterize256 and clusterize256x.
//
// * The former ingests all hashes in memory. It produces cluster sizes as
//   output. It's slower and is nice for one-stop shopping on a few thousand
//   hashes.
//
// * The latter is streaming, uses less memory, and is far faster. It does not
//   produce cluster sizes on output. (Those need to be computed as an
//   afterpass.) It necessary for operating on millions of hashes.
//
// A 'greedy' clusterer is used: given first-encountered hash h1, all subsequent
// hashes within the specified distance threshold of h1 are listed within that
// cluster. Another hash, call it h2, even if just outside h1's radius will be
// put in another cluster. Any hashes in the 'overlap' (within threshold of h1
// and h2) will *only* be listed in h1's clsuter, not h2's. This means if there
// are N hashes as input, this program lists N hashes as output.
//
// See hashio.h for file-format information.
//
// See the usage function for more usage information.
// ================================================================

using namespace facebook::pdq::hashing;
using namespace facebook::pdq::index;

const int DEFAULT_PDQ_DISTANCE_THRESHOLD = 31;

// ----------------------------------------------------------------
static void handle_fp(
    FILE* fp,
    MIH256<std::string>& mih,
    std::map<Hash256, int>& centersToIndices,
    int distanceThreshold,
    int& counter,
    int& insertionClusterIndex,
    int& matchClusterIndex,
    int traceCount,
    bool doBruteForceQuery);

// ----------------------------------------------------------------
static void usage(char* argv0, int rc) {
  FILE* fp = (rc == 0) ? stdout : stderr;
  fprintf(fp, "Usage: %s  [options] {zero or more hash-files}\n", argv0);
  fprintf(fp, "If zero filenames are provided, stdin is read.\n");
  fprintf(fp, "Files should have one hex-formatted 256-bit hash per line,\n");
  fprintf(fp, "optionally prefixed by \"hash=\". If a comma and other text\n");
  fprintf(fp, "follows the hash, it is used as metadata; else, a counter is\n");
  fprintf(fp, "used as the metadata.\n");
  fprintf(fp, "\n");
  fprintf(fp, "Options:\n");
  fprintf(fp, "-h|--help    Print this message.\n");
  fprintf(fp, "-b|--brute-force-query Use linear search not MIH.\n");
  fprintf(
      fp,
      "-d {n}       Distance threshold: default %d.\n",
      DEFAULT_PDQ_DISTANCE_THRESHOLD);
  fprintf(fp, "--trace {n}  Print to stderr every n items. Default off.\n");
  exit(rc);
}

// ----------------------------------------------------------------
int main(int argc, char** argv) {
  int doBruteForceQuery = false;
  int distanceThreshold = DEFAULT_PDQ_DISTANCE_THRESHOLD;
  int traceCount = 0;

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Parse command-line flags. I'm explicitly not using gflags or other such
  // libraries, to minimize the number of external dependencies for this
  // project.
  int argi = 1;
  while (argi < argc) {
    if (argv[argi][0] != '-') {
      break;
    } else if (!strcmp(argv[argi], "-h") || !strcmp(argv[argi], "--help")) {
      usage(argv[0], 0);
    } else if (
        !strcmp(argv[argi], "-b") ||
        !strcmp(argv[argi], "--brute-force-query")) {
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
    } else if (!strcmp(argv[argi], "--trace")) {
      if ((argc - argi) < 2) {
        usage(argv[0], 1);
      }
      if (sscanf(argv[argi + 1], "%d", &traceCount) != 1) {
        usage(argv[0], 1);
      }
      argi += 2;

    } else {
      usage(argv[0], 1);
    }
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  MIH256<std::string> mih;
  std::map<Hash256, int> centersToIndices;
  int insertionClusterIndex = 0;
  int matchClusterIndex = 0;

  int counter = 0;
  if (argi == argc) {
    handle_fp(
        stdin,
        mih,
        centersToIndices,
        distanceThreshold,
        counter,
        insertionClusterIndex,
        matchClusterIndex,
        traceCount,
        doBruteForceQuery);
  } else {
    for (; argi < argc; argi++) {
      char* filename = argv[argi];
      FILE* fp = fopen(filename, "r");
      if (fp == nullptr) {
        perror("fopen");
        fprintf(stderr, "Could not open \"%s\" for read.\n", filename);
        exit(1);
      }

      handle_fp(
          fp,
          mih,
          centersToIndices,
          distanceThreshold,
          counter,
          insertionClusterIndex,
          matchClusterIndex,
          traceCount,
          doBruteForceQuery);

      fclose(fp);
    }
  }

  return 0;
}

// ----------------------------------------------------------------
static void handle_fp(
    FILE* fp,
    MIH256<std::string>& mih,
    std::map<Hash256, int>& centersToIndices,
    int distanceThreshold,
    int& counter,
    int& insertionClusterIndex,
    int& matchClusterIndex,
    int traceCount,
    bool doBruteForceQuery) {
  Hash256 hash;
  std::string metadata;

  while (facebook::pdq::io::loadHashAndMetadataFromStream(
      fp, hash, metadata, counter)) {
    if (traceCount > 0) {
      if ((counter % traceCount) == 0) {
        fprintf(stderr, "-- %d\n", counter);
      }
    }
    counter++;

    std::vector<std::pair<Hash256, std::string>> matches;
    if (doBruteForceQuery) {
      mih.bruteForceQueryAll(hash, distanceThreshold, matches);
    } else {
      mih.queryAll(hash, distanceThreshold, matches);
    }

    Hash256& center = hash;
    int is_center = 0;
    if (matches.size() == 0) {
      is_center = 1;
      mih.insert(hash, metadata);
      centersToIndices.emplace(hash, insertionClusterIndex);
      matchClusterIndex = insertionClusterIndex;
      insertionClusterIndex++;
    } else {
      center = matches[0].first;
      matchClusterIndex = centersToIndices[center];
    }

    printf(
        "clidx=%d,hash1=%s,hash2=%s,is_center=%d,d=%d,%s\n",
        matchClusterIndex,
        hash.format().c_str(),
        center.format().c_str(),
        is_center,
        center.hammingDistance(hash),
        metadata.c_str());
  }
}
