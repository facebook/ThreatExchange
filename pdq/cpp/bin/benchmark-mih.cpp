#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pdq/cpp/index/mih.h>
#include <pdq/cpp/io/hashio.h>

#include <chrono>
#include <set>
#include <random>
#include <algorithm>

// ================================================================
// Static function declarations
static void usage(char* argv0, int rc);
static void do_test(char* argv0, int argc, char** argv);

// Helper function to generate random hashes
static facebook::pdq::hashing::Hash256 generateRandomHash(std::mt19937& gen) {
  facebook::pdq::hashing::Hash256 hash;
  std::uniform_int_distribution<uint16_t> dist(0, UINT16_MAX);
  
  for (int i = 0; i < facebook::pdq::hashing::HASH256_NUM_WORDS; i++) {
    hash.w[i] = dist(gen);
  }
  return hash;
}

// Add noise to hash by flipping random bits
static facebook::pdq::hashing::Hash256 addNoise(
  const facebook::pdq::hashing::Hash256& original,
  int numBitsToFlip,
  std::mt19937& gen) {
  
  facebook::pdq::hashing::Hash256 noisy = original;
  std::uniform_int_distribution<int> wordDist(0, facebook::pdq::hashing::HASH256_NUM_WORDS - 1);
  std::uniform_int_distribution<int> bitDist(0, 15); // Each word is 16 bits
  for (int i = 0; i < numBitsToFlip; i++) {
    int wordIndex = wordDist(gen);
    int bitIndex = bitDist(gen);
    // Flip bit with xor
    noisy.w[wordIndex] ^= (1 << bitIndex);
  }
  return noisy;
}

// ----------------------------------------------------------------
int main(int argc, char** argv) {
  if (argc>1 && (!strcmp(argv[1], "-h") || !strcmp(argv[1], "--help"))) {
    usage(argv[0], 0);
  } else {
    do_test(argv[0], argc - 1, argv + 1);
  }
  return 0;
}

// ----------------------------------------------------------------
static void usage(char* argv0, int rc) {
  FILE* fp = (rc == 0) ? stdout : stderr;
  fprintf(fp, "Usage: %s [options]\n", argv0);
  fprintf(fp, "Options:\n");
  fprintf(fp, "  -v                    Verbose output\n");
  fprintf(fp, "  --no-timings          Disable timing output\n");
  fprintf(fp, "  --seed N              Random seed (default: 41)\n");
  fprintf(fp, "  --haystack-size N     Number of hashes in haystack (default: 10000)\n");
  fprintf(fp, "  --needles-size N      Number of needle hashes (default: 1000)\n");
  fprintf(fp, "  --distance N          Maximum Hamming distance (default: 32)\n");
  exit(rc);
}

static void do_test(char* argv0, int argc, char** argv) {
  int maxDistance = 32;
  bool verbose = false;
  unsigned int seed = 41;
  size_t haystackSize = 10000;
  size_t needlesSize = 1000;
  int maxBitsToFlip = maxDistance - 1;

  // Parse command line arguments
  for (int i = 0; i < argc; i++) {
    std::string arg = argv[i];
    if (arg == "-v") {
      verbose = true;
    } else if (arg == "--seed") {
      if (i + 1 < argc) seed = std::stoi(argv[++i]);
    } else if (arg == "--haystack-size") {
      if (i + 1 < argc) haystackSize = std::stoi(argv[++i]);
    } else if (arg == "--needles-size") {
      if (i + 1 < argc) needlesSize = std::stoi(argv[++i]);
    } else if (arg == "--distance") {
      maxDistance = std::stoi(argv[++i]);
    } else {
      usage(argv0, 1);
      return;
    }
  }

  // Initialize random number generator
  std::mt19937 gen(seed);
  
  // Generate random hashes for needles
  std::vector<std::pair<facebook::pdq::hashing::Hash256, std::string>> needles;
  for (size_t i = 0; i < needlesSize; i++) {
    auto hash = generateRandomHash(gen);
    needles.push_back({hash, "needle_" + std::to_string(i)});
  }

  // Generate random hashes for haystack
  std::vector<std::pair<facebook::pdq::hashing::Hash256, std::string>> haystack;
  for (size_t i = 0; i < haystackSize; i++) {
    auto hash = generateRandomHash(gen);
    haystack.push_back({hash, "haystack_" + std::to_string(i)});
  }

  std::uniform_int_distribution<int> noiseDist(1, maxBitsToFlip);
  for (const auto& needle : needles) {
    int bitsToFlip = noiseDist(gen);
    auto noisyHash = addNoise(needle.first, bitsToFlip, gen);
    haystack.push_back({noisyHash, needle.second + "_noisy"});
  }
  std::shuffle(haystack.begin(), haystack.end(), gen);

  // Build the MIH
  std::vector<std::pair<facebook::pdq::hashing::Hash256, std::string>> matches;
  int num_matches = 0;

  std::chrono::time_point<std::chrono::steady_clock> t1, t2;
  std::chrono::duration<double> elapsed_seconds_outer;
  double seconds;

  facebook::pdq::index::MIH256<std::string> mih;

  t1 = std::chrono::system_clock::now();
  for (const auto& it : haystack) {
    mih.insert(it.first, it.second);
  }
  t2 = std::chrono::system_clock::now();
  elapsed_seconds_outer = t2 - t1;
  seconds = elapsed_seconds_outer.count();
  printf("\n");
  if (verbose) {
    printf("\n");
    mih.dump();
    printf("\n");
  }

  if (verbose) {
    printf("NEEDLES:\n");
    for (const auto& it : needles) {
      printf("%s,%s\n", it.first.format().c_str(), it.second.c_str());
    }
    printf("\n");

    printf("ORIGINAL HAYSTACK:\n");
    for (const auto& it : haystack) {
      printf("%s,%s\n", it.first.format().c_str(), it.second.c_str());
    }
    printf("\n");
  }

  // Do linear searches
  matches.clear();
  num_matches = 0;

  t1 = std::chrono::system_clock::now();
  for (const auto& it : needles) {
    mih.bruteForceQueryAll(it.first, maxDistance, matches);
  }
  num_matches = matches.size();
  t2 = std::chrono::system_clock::now();
  elapsed_seconds_outer = t2 - t1;
  seconds = elapsed_seconds_outer.count();

  printf("BRUTE-FORCE QUERY:\n");
  printf("NEEDLE COUNT:               %d\n", (int)needles.size());
  printf("HAYSTACK COUNT:             %d\n", (int)mih.size());
  printf("TOTAL MATCH COUNT:          %d\n", (int)num_matches);
  printf("SECONDS:                    %.6lf\n", seconds);
  printf("SECONDS PER MATCH:          %.6lf\n", num_matches > 0 ? seconds / num_matches : 0);
  printf("\n");

  // Do indexed searches
  matches.clear();
  num_matches = 0;

  t1 = std::chrono::system_clock::now();
  for (const auto& it : needles) {
    mih.queryAll(it.first, maxDistance, matches);
  }
  num_matches = matches.size();
  t2 = std::chrono::system_clock::now();
  elapsed_seconds_outer = t2 - t1;
  seconds = elapsed_seconds_outer.count();

  printf("MIH QUERY:\n");
  printf("NEEDLE COUNT:               %d\n", (int)needles.size());
  printf("HAYSTACK COUNT:             %d\n", (int)mih.size());
  printf("TOTAL MATCH COUNT:          %d\n", (int)num_matches);
  printf("SECONDS:                    %.6lf\n", seconds);
  printf("SECONDS PER MATCH:          %.6lf\n", num_matches > 0 ? seconds / num_matches : 0);
  printf("\n");
}
