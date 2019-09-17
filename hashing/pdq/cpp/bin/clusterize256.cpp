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
// By default, a 'snowball' clusterer is used: given first-encountered hash h1,
// all subsequent hashes within the specified distance threshold of h1 are
// listed within that cluster. This is transitive: if h1 is near h2, h2 is
// near h3, and h3 is near h4, then all four are clustered together even if
// h1 is not near h4.
//
// The non-snowball option means that for each hash, all other hashes within
// specified radius are printed. This allows for duplicate outputs.
//
// See hashio.h for file-format information.
//
// See the usage function for more usage information.
// ================================================================

using namespace facebook::pdq::hashing;
using namespace facebook::pdq::index;

const int DEFAULT_PDQ_DISTANCE_THRESHOLD = 31;

static void snowballClusterize(
    std::vector<std::pair<Hash256, std::string>>& vector_of_pairs,
    MIH256<std::string>& mih,
    bool separateClusters,
    int traceCount,
    bool doBruteForceQuery,
    int distanceThreshold);

static void radiallyClusterize(
    std::vector<std::pair<Hash256, std::string>>& vector_of_pairs,
    MIH256<std::string>& mih,
    bool separateClusters,
    int traceCount,
    bool doBruteForceQuery,
    int distanceThreshold);

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
  fprintf(fp, "-s|--separate-clusters Print a blank line between clusters.\n");
  fprintf(fp, "--snowball Print each hash once, with transitive clustering.\n");
  fprintf(fp, "  This is the default.\n");
  fprintf(
      fp,
      "--non-snowball For each hash, print all other hashes within "
      "distance threshold.\n");
  fprintf(
      fp,
      "-d {n}       Distance threshold: default %d.\n",
      DEFAULT_PDQ_DISTANCE_THRESHOLD);
  fprintf(fp, "--trace {n}  Print to stderr every n items. Default off.\n");
  exit(rc);
}

// ----------------------------------------------------------------
int main(int argc, char** argv) {
  bool verbose = false;
  bool separateClusters = false;
  bool snowball = true;
  int traceCount = 0;
  bool doBruteForceQuery = false;
  int distanceThreshold = DEFAULT_PDQ_DISTANCE_THRESHOLD;

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
    } else if (!strcmp(argv[argi], "--snowball")) {
      snowball = true;
      argi++;
    } else if (!strcmp(argv[argi], "--non-snowball")) {
      snowball = false;
      argi++;
    } else if (!strcmp(argv[argi], "-b")) {
      doBruteForceQuery = true;
      argi++;
    } else if (!strcmp(argv[argi], "--brute-force-query")) {
      doBruteForceQuery = true;
      argi++;
    } else if (
        !strcmp(argv[argi], "-s") ||
        !strcmp(argv[argi], "--separate_clusters") ||
        !strcmp(argv[argi], "--separate-clusters")) {
      separateClusters = true;
      argi++;

    } else if (!strcmp(argv[argi], "-d")) {
      if ((argc - argi) < 2)
        usage(argv[0], 1);
      if (sscanf(argv[argi + 1], "%d", &distanceThreshold) != 1) {
        usage(argv[0], 1);
      }
      argi += 2;
    } else if (!strcmp(argv[argi], "--trace")) {
      if ((argc - argi) < 2)
        usage(argv[0], 1);
      if (sscanf(argv[argi + 1], "%d", &traceCount) != 1) {
        usage(argv[0], 1);
      }
      argi += 2;

    } else {
      usage(argv[0], 1);
    }
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Load input hashes+metadata

  std::vector<std::pair<Hash256, std::string>> vector_of_pairs;

  facebook::pdq::io::loadHashesAndMetadataFromFiles(
      &argv[argi], argc - argi, vector_of_pairs);

  if (verbose) {
    printf("ORIGINAL VECTOR OF PAIRS:\n");
    for (auto it : vector_of_pairs) {
      Hash256 hash = it.first;
      std::string metadata = it.second;
      printf("%s,%s\n", hash.format().c_str(), metadata.c_str());
    }
    printf("\n");
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Build the mutually-indexed hash

  MIH256<std::string> mih;
  // We could insertAll, but instead loop so we can trace.
  // mih.insertAll(vector_of_pairs);
  int i = 0;
  for (auto it : vector_of_pairs) {
    if (traceCount > 0) {
      if ((i % traceCount) == 0) {
        fprintf(stderr, "i %d\n", i);
      }
    }
    i++;
    mih.insert(it.first, it.second);
  }

  if (verbose) {
    printf("MIH:\n");
    mih.dump();
    printf("\n");
  }

  //  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  // Clusterize

  if (snowball) {
    snowballClusterize(
        vector_of_pairs,
        mih,
        separateClusters,
        traceCount,
        doBruteForceQuery,
        distanceThreshold);
  } else {
    radiallyClusterize(
        vector_of_pairs,
        mih,
        separateClusters,
        traceCount,
        doBruteForceQuery,
        distanceThreshold);
  }

  return 0;
}

// ----------------------------------------------------------------
static void snowballClusterize(
    std::vector<std::pair<Hash256, std::string>>& vector_of_pairs,
    MIH256<std::string>& mih,
    bool separateClusters,
    int traceCount,
    bool doBruteForceQuery,
    int distanceThreshold) {
  std::map<std::string, std::set<std::string>> adjacency_matrix;
  std::map<std::string, Hash256> metadata_to_hashes;

  // INGEST DATA
  int i = 0;
  for (auto it1 : vector_of_pairs) {
    Hash256& needle_hash = it1.first;
    std::string& needle_metadata = it1.second;

    if (traceCount > 0) {
      if ((i % traceCount) == 0) {
        fprintf(stderr, "o %d\n", i);
      }
    }
    i++;

    std::vector<std::pair<Hash256, std::string>> matches;
    if (doBruteForceQuery) {
      mih.bruteForceQueryAll(needle_hash, distanceThreshold, matches);
    } else {
      mih.queryAll(needle_hash, distanceThreshold, matches);
    }

    metadata_to_hashes[needle_metadata] = needle_hash;
    for (const auto& it2 : matches) {
      const Hash256& haystack_hash = it2.first;
      const std::string& haystack_metadata = it2.second;
      metadata_to_hashes[haystack_metadata] = haystack_hash;
      adjacency_matrix[needle_metadata].insert(haystack_metadata);
      adjacency_matrix[haystack_metadata].insert(needle_metadata);
    }
  }

  // IDENTIFY CLUSTER REPRESENTATIVES

  // For the sake of discussion suppose the item IDs are A, B, C, D, E.
  // Input data includes the adjacency matrix
  //
  //     A B C D E
  //   A * . * * .
  //   B . * . * .
  //   C * . * . .
  //   D * * . * .
  //   E . . . . *
  //
  // We expect to get [A,B,C,D] as one equivalence class and [E] as the other.
  // Representatives are just the first-found, e.g. A and E respectively.

  std::map<std::string, std::string> metadatas_to_cluster_representatives;

  // For each row of the adjacency matrix:
  for (const auto& row_it : adjacency_matrix) {
    const std::string& metadata_i = row_it.first;
    const std::set<std::string>& metadata_js = row_it.second;

    // Already-visited items, found by off-diagonal on a previous row
    if (metadatas_to_cluster_representatives.find(metadata_i) !=
        metadatas_to_cluster_representatives.end()) {
      continue;
    }

    // Each row of the adjacency matrix contributes to an equivalence class.
    // E.g. the top row of the above example gives [A,C,D]. The only question
    // is whether this is standalone or part of something already seen. For
    // example, on the first row we get [A,C,D]. On the second row we have
    // [B,D] but D was already seen.

    // Find a representative for this item: Either the first-found in the
    // row, or an already-seen (if there is one).
    std::string representative = metadata_i; // E.g. A on 1st row, B on 2nd row
    for (const std::string& metadata_j : metadata_js) {
      if (metadatas_to_cluster_representatives.find(metadata_j) !=
          metadatas_to_cluster_representatives.end()) {
        representative = metadatas_to_cluster_representatives[metadata_j];
        break;
      }
    }

    // Mark all the items in the current row as having that representative
    for (const std::string& metadata_j : metadata_js) {
      metadatas_to_cluster_representatives[metadata_j] = representative;
    }
  }

  // FORM EQUIVALENCE CLASSES
  std::map<std::string, std::set<std::string>> equivalence_classes;
  for (const auto& it : metadata_to_hashes) {
    const std::string& metadata = it.first;
    std::string& representative =
        metadatas_to_cluster_representatives[metadata];
    equivalence_classes[representative].insert(metadata);
  }

  // OUTPUT
  int clusterIndex = 0;
  for (const auto& it : equivalence_classes) {
    const std::set<std::string>& equivalence_class = it.second;
    clusterIndex++;
    int clusterSize = equivalence_class.size();

    if (separateClusters && clusterIndex > 1) {
      printf("\n");
    }

    for (const std::string& metadata : equivalence_class) {
      printf(
          "clidx=%d,clusz=%d,hash=%s,%s\n",
          clusterIndex,
          clusterSize,
          metadata_to_hashes[metadata].format().c_str(),
          metadata.c_str());
    }
  }
}

// ----------------------------------------------------------------
static void radiallyClusterize(
    std::vector<std::pair<Hash256, std::string>>& vector_of_pairs,
    MIH256<std::string>& mih,
    bool separateClusters,
    int traceCount,
    bool doBruteForceQuery,
    int distanceThreshold) {
  int clusterIndex = 0;

  int i = 0;
  for (auto it1 : vector_of_pairs) {
    Hash256& needle_hash = it1.first;

    if (traceCount > 0) {
      if ((i % traceCount) == 0) {
        fprintf(stderr, "o %d\n", i);
      }
    }
    i++;

    std::vector<std::pair<Hash256, std::string>> matches;
    if (doBruteForceQuery) {
      mih.bruteForceQueryAll(needle_hash, distanceThreshold, matches);
    } else {
      mih.queryAll(needle_hash, distanceThreshold, matches);
    }

    int clusterSize = matches.size();
    if (clusterSize > 0) {
      clusterIndex++;
      if (clusterIndex > 1 && separateClusters) {
        printf("\n");
      }
      for (const auto& it2 : matches) {
        const Hash256& haystack_hash = it2.first;
        const std::string& haystack_metadata = it2.second;
        int d = needle_hash.hammingDistance(haystack_hash);
        printf(
            "clidx=%d,clusz=%d,hash1=%s,hash2=%s,d=%d,%s\n",
            clusterIndex,
            clusterSize,
            needle_hash.format().c_str(),
            haystack_hash.format().c_str(),
            d,
            haystack_metadata.c_str());
      }
    }

    fflush(stdout);
  }
}
