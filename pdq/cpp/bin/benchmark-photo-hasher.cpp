#ifndef _GNU_SOURCE
#define _GNU_SOURCE
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pdq/cpp/io/hashio.h>
#include <pdq/cpp/io/pdqio.h>

#include <chrono>

using namespace facebook::pdq::hashing;

// ================================================================
// Static function declarations
static void usage(char* argv0, int rc);
static void hash(char* argv0, int argc, char** argv);

// ----------------------------------------------------------------
int main(int argc, char** argv) {
  if (argc > 1 && (!strcmp(argv[1], "-h") || !strcmp(argv[1], "--help"))) {
    usage(argv[0], 0);
  } else {
    hash(argv[0], argc - 1, argv + 1);
  }
  return 0;
}

// ----------------------------------------------------------------
static void usage(char* argv0, int rc) {
  FILE* fp = (rc == 0) ? stdout : stderr;
  fprintf(fp, "Usage: %s [options] folder_path\n", argv0);
  fprintf(fp, "Options:\n");
  fprintf(fp, "  -v               Verbose output\n");
  fprintf(
      fp,
      "  -n N             Total number of hashes to generate, can be more or less than the number of images in the folder\n");
  fprintf(
      fp,
      "                           (default: 0, meaning generate one hash for each image in the folder)\n");
  fprintf(
      fp,
      "  --dihedral       Compute dihedral versions of the hashes (default: false)\n");
  exit(rc);
}

static void hash(char* argv0, int argc, char** argv) {
  std::string folderPath;
  int numHashes = 0;
  bool verbose = false;
  bool dihedral = false;

  // Parse command line arguments
  for (int i = 0; i < argc; i++) {
    std::string arg = argv[i];
    if (arg == "-v") {
      verbose = true;
    } else if (arg == "-n") {
      if (i + 1 < argc) {
        numHashes = std::stoi(argv[++i]);
      } else {
        fprintf(stderr, "Error: Missing argument for -n\n");
        usage(argv0, 1);
        return;
      }
    } else if (arg == "--dihedral") {
      dihedral = true;
    } else if (arg == "-h" || arg == "--help") {
      usage(argv0, 0);
      return;
    } else if (i == argc - 1) {
      folderPath = arg;
    } else {
      fprintf(stderr, "Unknown argument: %s\n", arg.c_str());
      usage(argv0, 1);
      return;
    }
  }

  // Generate hashes
  std::vector<facebook::pdq::hashing::Hash256> hashes;
  float totalReadSeconds = 0, totalHashSeconds = 0;
  int numErrors = 0, numSuccesses = 0;
  DIR* dir = opendir(folderPath.c_str());
  if (dir == NULL) {
    perror("opendir");
    return;
  }
  struct dirent* ent;
  while (true) {
    while ((ent = readdir(dir)) != NULL) {
      std::string filePath = folderPath + "/" + ent->d_name;
      if (ent->d_type == DT_REG) {
        facebook::pdq::hashing::Hash256 hash;
        int quality;
        int imageHeightTimesWidth;
        float readSeconds;
        float hashSeconds;
        const char* filename = filePath.c_str();
        bool success;
        if (dihedral) {
          facebook::pdq::hashing::Hash256 hashRotate90, hashRotate180,
              hashRotate270, hashFlipX, hashFlipY, hashFlipPlus1,
              hashFlipMinus1;
          success = facebook::pdq::hashing::pdqDihedralHash256esFromFile(
              filename,
              &hash,
              &hashRotate90,
              &hashRotate180,
              &hashRotate270,
              &hashFlipX,
              &hashFlipY,
              &hashFlipPlus1,
              &hashFlipMinus1,
              quality,
              imageHeightTimesWidth,
              readSeconds,
              hashSeconds);
        } else {
          success = facebook::pdq::hashing::pdqHash256FromFile(
              filename,
              hash,
              quality,
              imageHeightTimesWidth,
              readSeconds,
              hashSeconds);
        }
        if (!success) {
          numErrors++;
          fprintf(stderr, "Error reading file: %s\n", filename);
          continue;
        }
        if (verbose) {
          printf("File: %s\n", filename);
          printf("Hash: %s\n", hash.format().c_str());
          printf("Quality: %d\n", quality);
          printf("Image height * width: %d\n", imageHeightTimesWidth);
          printf("Read seconds: %.6lf\n", readSeconds);
          printf("Hash seconds: %.6lf\n", hashSeconds);
          printf("\n");
        }
        hashes.push_back(hash);
        totalReadSeconds += readSeconds;
        totalHashSeconds += hashSeconds;
        numSuccesses++;
        if (numSuccesses == numHashes)
          break;
      }
    }
    if (numSuccesses == 0) {
      fprintf(stderr, "No images found in folder: %s\n", folderPath.c_str());
      return;
    }
    if (numHashes == 0 || numSuccesses == numHashes)
      break;
    closedir(dir);
    dir = opendir(folderPath.c_str());
  }

  printf("PHOTO COUNT:               %d\n", (int)hashes.size());
  if (dihedral) {
    printf("TOTAL DIHEDRAL HASHES (8/PHOTO):     %d\n", (int)hashes.size() * 8);
  }
  printf("ERROR COUNT:               %d\n", numErrors);
  printf("TIME SPENT HASHING PHOTOS (SECONDS):     %.6lf\n", totalHashSeconds);
  double photosHashedPerSecond =
      totalHashSeconds > 0 ? numSuccesses / totalHashSeconds : 0;
  printf("PHOTOS HASHED PER SECOND:   %.6lf\n", photosHashedPerSecond);

  printf(
      "TIME SPENT READING PHOTOS (SECONDS):        %.6lf\n", totalReadSeconds);
  double photosReadPerSecond =
      totalReadSeconds > 0 ? numSuccesses / totalReadSeconds : 0;
  printf("PHOTOS READ PER SECOND:     %.6lf\n", photosReadPerSecond);
  printf("\n");
}