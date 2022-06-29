#include <cstring>
#include <pdq/cpp/io/hashio.h>
#include <vpdq/cpp/hashing/vpdqHashType.h>
#include <vpdq/cpp/io/vpdqio.h>

using namespace std;
using namespace facebook;

static void usage(char* argv0, int rc) {
  FILE* fp = (rc == 0) ? stdout : stderr;
  fprintf(
      fp,
      "Usage: %s [options] file1name file2name hamming_distanceTolerance qualityTolerance\n",
      argv0);
  fprintf(fp, "Options:\n");
  fprintf(fp, "-v|--verbose: Show all hash matching information\n");
  exit(rc);
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
    if (!strcmp(argv[argi], "-v") || !strcmp(argv[argi], "--verbose")) {
      verbose = true;
      continue;
    }
  }

  if (argi > argc - 4) {
    usage(argv[0], 1);
  }

  vector<facebook::vpdq::hashing::vpdqFeature> video1Hashes;
  vector<facebook::vpdq::hashing::vpdqFeature> video2Hashes;
  bool ret = facebook::vpdq::io::loadHashesFromFileOrDie(
      argv[argi], video1Hashes, argv[0]);
  if (!ret) {
    return -1;
  }
  ret = facebook::vpdq::io::loadHashesFromFileOrDie(
      argv[argi + 1], video2Hashes, argv[0]);
  if (!ret) {
    return -1;
  }

  distanceTolerance = atoi(argv[argi + 2]);
  qualityTolerance = atoi(argv[argi + 3]);

  if (video1Hashes.size() != video2Hashes.size()) {
    fprintf(
        stderr,
        "VideoHashes1 size %lu doesn't match with VideoHashes2 size %lu\n",
        video1Hashes.size(),
        video2Hashes.size());
    return 1;
  }
  size_t count = 0;
  size_t total_hashed_compared = 0;
  for (size_t i = 0; i < video1Hashes.size(); i++) {
    if (video1Hashes[i].quality < qualityTolerance ||
        video2Hashes[i].quality < qualityTolerance) {
      if (verbose) {
        printf(
            "Skipping Line %zu Hash1: %s Hash2: %s, because of low quality Hash1: %d Hash2: %d \n",
            i,
            video1Hashes[i].pdqHash.format().c_str(),
            video2Hashes[i].pdqHash.format().c_str(),
            video1Hashes[i].quality,
            video2Hashes[i].quality);
      }
      continue;
    }
    total_hashed_compared++;
    if (video1Hashes[i].pdqHash.hammingDistance(video2Hashes[i].pdqHash) <
        distanceTolerance) {
      count++;
      if (verbose) {
        printf(
            "Line %zu Hash1: %s Hash2: %s match \n",
            i,
            video1Hashes[i].pdqHash.format().c_str(),
            video2Hashes[i].pdqHash.format().c_str());
      }
    } else {
      if (verbose) {
        printf(
            "NO MATCH: Line %zu Hash1: %s Hash2: %s\n",
            i,
            video1Hashes[i].pdqHash.format().c_str(),
            video2Hashes[i].pdqHash.format().c_str());
      }
    }
  }
  printf(
      "%3f Percentage  matches\n", (float)count * 100 / total_hashed_compared);
  return 0;
}
