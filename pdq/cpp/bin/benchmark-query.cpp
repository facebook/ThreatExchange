// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pdq/cpp/common/pdqutils.h>
#include <pdq/cpp/index/flat.h>
#include <pdq/cpp/index/mih.h>
#include <pdq/cpp/io/hashio.h>

#include <algorithm>
#include <array>
#include <random>
#include <set>

// ================================================================

// Benchmark result structure
struct BenchmarkResult {
  std::string method;
  int queryCount;
  int indexCount;
  int totalMatchCount;
  double totalQuerySeconds;
};

// Static function declarations
static void usage(char* argv0, int rc);
static void query(char* argv0, int argc, char** argv);

// Function declarations for each query method
static BenchmarkResult queryLinear(
    const int maxDistance,
    const bool verbose,
    const unsigned int seed,
    const size_t indexSize,
    const size_t querySize,
    const std::vector<std::array<facebook::pdq::hashing::Hash256, 8>>& queries,
    const std::vector<facebook::pdq::hashing::Hash256>& index);
static BenchmarkResult queryMIH(
    const int maxDistance,
    const bool verbose,
    const unsigned int seed,
    const size_t indexSize,
    const size_t querySize,
    const std::vector<std::array<facebook::pdq::hashing::Hash256, 8>>& queries,
    const std::vector<facebook::pdq::hashing::Hash256>& index);

// ----------------------------------------------------------------
int main(int argc, char** argv) {
  if (argc > 1 && (!strcmp(argv[1], "-h") || !strcmp(argv[1], "--help"))) {
    usage(argv[0], 0);
  } else {
    query(argv[0], argc - 1, argv + 1);
  }
  return 0;
}

// ----------------------------------------------------------------
static void usage(char* argv0, int rc) {
  FILE* fp = (rc == 0) ? stdout : stderr;
  fprintf(fp, "Usage: %s [options]\n", argv0);
  fprintf(fp, "Options:\n");
  fprintf(fp, "  -v               Verbose output\n");
  fprintf(fp, "  --seed N         Random seed (default: 41)\n");
  fprintf(fp, "  -q N             Number of queries to run (default: 1000)\n");
  fprintf(
      fp,
      "  -b N             Number of PDQ hashes to query against (default: 10000)\n");
  fprintf(
      fp,
      "  -d N             Maximum Hamming distance for matches (default: 31)\n");
  fprintf(
      fp,
      "  -m               Method for querying (default: linear), Available: linear, mih\n");
  exit(rc);
}

static void query(char* argv0, int argc, char** argv) {
  int maxDistance = 31;
  bool verbose = false;
  unsigned int seed = 41;
  size_t indexSize = 10000;
  size_t querySize = 1000;
  std::string method = "linear";

  // Parse command line arguments
  for (int i = 0; i < argc; i++) {
    std::string arg = argv[i];
    if (arg == "-q") {
      if (i + 1 < argc) {
        querySize = std::stoi(argv[++i]);
      } else {
        fprintf(stderr, "Error: Missing argument for -q\n");
        usage(argv0, 1);
        return;
      }
    } else if (arg == "-b") {
      if (i + 1 < argc) {
        indexSize = std::stoi(argv[++i]);
      } else {
        fprintf(stderr, "Error: Missing argument for -b\n");
        usage(argv0, 1);
        return;
      }
    } else if (arg == "-d") {
      if (i + 1 < argc) {
        maxDistance = std::stoi(argv[++i]);
      } else {
        fprintf(stderr, "Error: Missing argument for -d\n");
        usage(argv0, 1);
        return;
      }
    } else if (arg == "--seed") {
      if (i + 1 < argc) {
        seed = std::stoi(argv[++i]);
      } else {
        fprintf(stderr, "Error: Missing argument for --seed\n");
        usage(argv0, 1);
        return;
      }
    } else if (arg == "-m") {
      if (i + 1 < argc) {
        std::string methodName = argv[++i];
        if (methodName == "linear" || methodName == "mih") {
          method = methodName;
        } else {
          fprintf(stderr, "Invalid method: %s\n", methodName.c_str());
          usage(argv0, 1);
          return;
        }
      }
    } else if (arg == "-v") {
      verbose = true;
    } else if (arg == "-h" || arg == "--help") {
      usage(argv0, 0);
      return;
    } else if (arg.length() > 0) {
      fprintf(stderr, "Unknown argument: %s\n", arg.c_str());
      usage(argv0, 1);
      return;
    }
  }

  // Initialize random number generator
  std::mt19937 gen(seed);

  // Generate random hashes for queries
  std::vector<std::array<facebook::pdq::hashing::Hash256, 8>> queries;
  for (size_t i = 0; i < querySize; i++) {
    std::array<facebook::pdq::hashing::Hash256, 8> hashes;
    for (size_t j = 0; j < 8; j++) {
      hashes[j] = facebook::pdq::hashing::generateRandomHash(gen);
    }
    queries.push_back(hashes);
  }

  // Generate random hashes for index
  std::vector<facebook::pdq::hashing::Hash256> index;
  const size_t numberOfRandomHashes =
      (indexSize > querySize * 8) ? indexSize - querySize * 8 : 0;
  for (size_t i = 0; i < numberOfRandomHashes; i++) {
    const auto hash = facebook::pdq::hashing::generateRandomHash(gen);
    index.push_back(hash);
  }

  // Add noise to queries then insert into index
  std::uniform_int_distribution<int> noiseDist(1, maxDistance);
  for (const auto& query : queries) {
    const auto dihedralToAdd = gen() % 8;
    for (size_t j = 0; j < 8; j++) {
      int bitsToFlip = noiseDist(gen);
      const auto noisyHash = facebook::pdq::hashing::addNoise(
          query[dihedralToAdd], bitsToFlip, gen);
      index.push_back(noisyHash);
    }
  }
  std::shuffle(index.begin(), index.end(), gen);

  if (verbose) {
    printf("GENERATED QUERIES:\n");
    for (const auto& it : queries) {
      for (size_t j = 0; j < 8; j++) {
        printf("%s\n", it[j].format().c_str());
      }
    }
    printf("\n");

    printf("GENERATED INDEX:\n");
    for (const auto& it : index) {
      printf("%s\n", it.format().c_str());
    }
    printf("\n");
  }

  BenchmarkResult result;
  if (method == "linear") {
    result = queryLinear(
        maxDistance, verbose, seed, indexSize, querySize, queries, index);
  } else if (method == "mih") {
    result = queryMIH(
        maxDistance, verbose, seed, indexSize, querySize, queries, index);
  } else {
    fprintf(stderr, "Unknown method: %s\n", method.c_str());
    usage(argv0, 1);
    return;
  }

  printf("METHOD: %s\n", result.method.c_str());
  printf(
      "QUERY COUNT:             %d * 8 = %d\n",
      result.queryCount,
      result.queryCount * 8);
  printf("INDEX COUNT:             %d\n", result.indexCount);
  printf("TOTAL MATCH COUNT:       %d\n", result.totalMatchCount);
  printf("TOTAL QUERY SECONDS:     %.6lf\n", result.totalQuerySeconds);
  double queriesPerSecond = result.totalQuerySeconds > 0
      ? result.queryCount / result.totalQuerySeconds
      : 0;
  printf("QUERIES PER SECOND:     %.2lf\n", queriesPerSecond);
  if (result.totalQuerySeconds > 0) {
    const double throughput =
        (result.queryCount / result.totalQuerySeconds) * 8 * index.size() / 1e6;
    printf("THROUGHPUT (millions of amortized tests/sec): %.2lf\n", throughput);
  }
  printf("\n");
}

///////////////////////
//// Query methods ////
///////////////////////

static BenchmarkResult queryLinear(
    const int maxDistance,
    const bool verbose,
    const unsigned int seed,
    const size_t indexSize,
    const size_t querySize,
    const std::vector<std::array<facebook::pdq::hashing::Hash256, 8>>& queries,
    const std::vector<facebook::pdq::hashing::Hash256>& index) {
  // Do linear searches
  std::vector<std::pair<size_t, size_t>> matches;

  Timer queryTimer("Linear query", verbose);
  for (const std::array<facebook::pdq::hashing::Hash256, 8>& it : queries) {
    const facebook::pdq::index::Flat flat(it);
    flat.queryAll(index.data(), index.size(), maxDistance, matches);
  }
  double seconds = queryTimer.elapsed();

  return {
      facebook::pdq::index::Flat::SIMD_ACCELERATED
          ? "linear query (SIMD accelerated)"
          : "linear query",
      static_cast<int>(queries.size()),
      static_cast<int>(index.size()),
      static_cast<int>(matches.size()),
      seconds,
  };
}

static BenchmarkResult queryMIH(
    const int maxDistance,
    const bool verbose,
    const unsigned int seed,
    const size_t indexSize,
    const size_t querySize,
    const std::vector<std::array<facebook::pdq::hashing::Hash256, 8>>& queries,
    const std::vector<facebook::pdq::hashing::Hash256>& index) {
  // Build the MIH
  facebook::pdq::index::MIH256<size_t> mih;

  size_t ix = 0;
  Timer insertTimer("MIH insert", verbose);
  for (const auto& it : index) {
    mih.insert(it, ix++);
  }
  double insertSeconds = insertTimer.elapsed();
  printf("MIH index build time: %.6lf\n", insertSeconds);

  printf("\n");
  if (verbose) {
    printf("\n");
    mih.dump();
    printf("\n");
  }

  // Do indexed searches
  std::vector<std::pair<facebook::pdq::hashing::Hash256, size_t>> matches;
  matches.clear();

  Timer queryTimer("MIH query", verbose);
  for (const auto& it : queries) {
    for (size_t j = 0; j < 8; j++) {
      mih.queryAll(it[j], maxDistance, matches);
    }
  }
  double seconds = queryTimer.elapsed();

  return {
      "mutually-indexed hashing query",
      static_cast<int>(queries.size()),
      static_cast<int>(mih.size()),
      static_cast<int>(matches.size()),
      seconds,
  };
}
