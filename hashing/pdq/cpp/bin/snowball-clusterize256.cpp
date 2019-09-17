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

// XXX UNDER CONSTRUCTION
// XXX UNDER CONSTRUCTION
// XXX UNDER CONSTRUCTION
// XXX UNDER CONSTRUCTION
// XXX UNDER CONSTRUCTION

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
// xxx more comments
//
// See hashio.h for file-format information.
//
// See the usage function for more usage information.
// ================================================================

using namespace facebook::pdq::hashing;

const int DEFAULT_PDQ_DISTANCE_THRESHOLD = 31;

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
  fprintf(fp, "-v|--verbose Be verbose.\n");
  fprintf(fp, "-b|--brute-force-query Use linear search not MIH.\n");
  fprintf(fp, "-d {n}       Distance threshold: default %d.\n",
    DEFAULT_PDQ_DISTANCE_THRESHOLD);
  fprintf(fp, "--trace {n}       Print to stderr every n items. Default off.\n");
  exit(rc);
}

// ----------------------------------------------------------------
int main(int argc, char** argv) {
  bool verbose = false;
  int  doBruteForceQuery = false;
  int  distanceThreshold = DEFAULT_PDQ_DISTANCE_THRESHOLD;
  int  traceCount = 0;

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
    } else if (!strcmp(argv[argi], "-v") || !strcmp(argv[argi], "--verbose")) {
      verbose = true;
      argi++;
    } else if (!strcmp(argv[argi], "-b")) {
      doBruteForceQuery = true;
      argi++;
    } else if (!strcmp(argv[argi], "--brute-force-query")) {
      doBruteForceQuery = true;
      argi++;

    } else if (!strcmp(argv[argi], "-d")) {
      if ((argc - argi) < 2)
        usage(argv[0], 1);
      if (sscanf(argv[argi+1], "%d", &distanceThreshold) != 1) {
        usage(argv[0], 1);
      }
      argi += 2;
    } else if (!strcmp(argv[argi], "--trace")) {
      if ((argc - argi) < 2)
        usage(argv[0], 1);
      if (sscanf(argv[argi+1], "%d", &traceCount) != 1) {
        usage(argv[0], 1);
      }
      argi += 2;

    } else {
      usage(argv[0], 1);
    }
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Load input hashes+metadata

  std::vector<std::pair<Hash256,std::string>> vector_of_pairs;

  facebook::pdq::io::loadHashesAndMetadataFromFiles(&argv[argi], argc-argi, vector_of_pairs);

  if (verbose) {
    printf("ORIGINAL VECTOR OF PAIRS:\n");
    for (auto it: vector_of_pairs) {
      Hash256 hash = it.first;
      std::string metadata = it.second;
      printf("%s,%s\n", hash.format().c_str(), metadata.c_str());
    }
    printf("\n");
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Build the mutually-indexed hash. Initially mark all hayfibers with
  // cluster ID -1.

  facebook::pdq::index::MIH256<std::pair<int,std::string>> mih;
  // We could insertAll, but instead loop so we can trace.
  // mih.insertAll(vector_of_pairs);
  int i = 0;
  for (auto it : vector_of_pairs) {
    Hash256& hash = it.first;
    std::string& metadata = it.second;
    if (traceCount > 0) {
      if ((i % traceCount) == 0) {
        fprintf(stderr, "i %d\n", i);
      }
    }
    i++;
    mih.insert(hash, std::make_pair(-1, metadata));
  }

  if (verbose) {
    printf("MIH:\n");
    mih.dump();
    printf("\n");
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Clusterize

  int newClusterIndex = 0;

  i = 0;
  for (auto& it1 : vector_of_pairs) {
    Hash256& needle_hash = it1.first;
    std::string needle_metadata = it1.second;

    std::vector<std::pair<Hash256,std::pair<int,std::string>>> matches;

    if (traceCount > 0) {
      if ((i % traceCount) == 0) {
        fprintf(stderr, "o %d\n", i);
      }
    }
    i++;

    if (doBruteForceQuery) {
      mih.bruteForceQueryAll(needle_hash, distanceThreshold, matches);
    } else {
      mih.queryAll(needle_hash, distanceThreshold, matches);
    }

    int matchedClusterIndex = -1;
    for (auto& it2 : matches) {
      auto& hay_cluster_id_and_metadata = it2.second;
      int& hay_cluster_index = hay_cluster_id_and_metadata.first;
      if (hay_cluster_index != -1) {
        matchedClusterIndex = hay_cluster_index;
        break;
      }
    }
    int assignedClusterIndex = (matchedClusterIndex == -1)
      ? ++newClusterIndex
      : matchedClusterIndex;
    for (auto& it2: matches) {
      printf("WRITE %d\n", assignedClusterIndex);
      it2.second.second = assignedClusterIndex;
    }
  }

  for (auto& it: mih.get()) {
    Hash256& hash = it.first;
    auto cluster_id_and_metadata = it.second;
    int clusterIndex = cluster_id_and_metadata.first;
    std::string metadata = cluster_id_and_metadata.second;

    printf("clidx=%d,hash=%s,%s\n",
      clusterIndex,
      hash.format().c_str(),
      metadata.c_str());

    fflush(stdout);
  }

  return 0;
}
