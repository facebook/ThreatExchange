// ================================================================
// Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved
// ================================================================

#include <pdq/cpp/io/hashio.h>

#include <stdlib.h>
#include <string.h>

namespace facebook {
namespace pdq {
namespace io {

// ----------------------------------------------------------------
// See comments in header file
bool loadHashAndMetadataFromStream(
    FILE* fp,
    facebook::pdq::hashing::Hash256& hash,
    std::string& metadata,
    int counter) {
  char prefix[] = "hash=";
  int prefix_length = strlen(prefix);
  char* line = nullptr;
  size_t linelen = 0;

  if ((ssize_t)(linelen = getline(&line, &linelen, fp)) == -1) {
    return false;
  }

  // Chomp
  if (linelen > 0) {
    if (line[linelen - 1] == '\n') {
      line[linelen - 1] = 0;
    }
  }

  // Split hash from metadata on comma
  char* cut = strchr(line, ',');
  if (cut == nullptr) {
    metadata = "idx=" + std::to_string(counter);
  } else {
    *cut = 0;
    metadata = std::string(&cut[1]);
  }
  if (!strncmp(line, prefix, prefix_length)) {
    hash =
        facebook::pdq::hashing::Hash256::fromStringOrDie(&line[prefix_length]);
  } else {
    hash = facebook::pdq::hashing::Hash256::fromStringOrDie(line);
  }
  return true;
}

// ----------------------------------------------------------------
// See comments in header file
void loadHashesAndMetadataFromStream(
    FILE* fp,
    std::vector<std::pair<facebook::pdq::hashing::Hash256, std::string>>&
        vector_of_pairs) {
  while (true) {
    int counter = vector_of_pairs.size() + 1;
    facebook::pdq::hashing::Hash256 hash;
    std::string metadata;
    bool rc = loadHashAndMetadataFromStream(fp, hash, metadata, counter);
    if (!rc) {
      break;
    }
    vector_of_pairs.push_back(std::make_pair(hash, metadata));
  }
}

// ----------------------------------------------------------------
bool loadHashesAndMetadataFromFile(
    char* filename,
    std::vector<std::pair<facebook::pdq::hashing::Hash256, std::string>>&
        vector_of_pairs) {
  FILE* fp = fopen(filename, "r");
  if (fp == nullptr) {
    perror("fopen");
    fprintf(stderr, "Could not open \"%s\" for read.\n", filename);
    return false;
  }
  loadHashesAndMetadataFromStream(fp, vector_of_pairs);
  (void)fclose(fp);
  return true;
}

// ----------------------------------------------------------------
bool loadHashesAndMetadataFromFiles(
    char** filenames,
    int num_filenames,
    std::vector<std::pair<facebook::pdq::hashing::Hash256, std::string>>&
        vector_of_pairs) {
  if (num_filenames == 0) {
    loadHashesAndMetadataFromStream(stdin, vector_of_pairs);
  } else {
    for (int i = 0; i < num_filenames; i++) {
      bool status =
          loadHashesAndMetadataFromFile(filenames[i], vector_of_pairs);
      if (status == false) {
        return false;
      }
    }
  }
  return true;
}

// ----------------------------------------------------------------
void loadHashesFromFilesOrDie(
    char** filenames,
    int num_filenames,
    std::vector<facebook::pdq::hashing::Hash256>& hashes) {
  if (num_filenames == 0) {
    loadHashesFromStream(stdin, hashes);
  } else {
    for (int i = 0; i < num_filenames; i++) {
      loadHashesFromFileOrDie(filenames[i], hashes);
    }
  }
}

// ----------------------------------------------------------------
void loadHashesFromFileOrDie(
    char* filename,
    std::vector<facebook::pdq::hashing::Hash256>& hashes) {
  if (!loadHashesFromFile(filename, hashes)) {
    // Error message already printed out
    exit(1);
  }
}

// ----------------------------------------------------------------
bool loadHashesFromFile(
    char* filename,
    std::vector<facebook::pdq::hashing::Hash256>& hashes) {
  FILE* fp = fopen(filename, "r");
  if (fp == nullptr) {
    perror("fopen");
    fprintf(stderr, "Could not open \"%s\" for read.\n", filename);
    return false;
  }
  loadHashesFromStream(fp, hashes);
  fclose(fp);
  return true;
}

// ----------------------------------------------------------------
void loadHashesFromStream(
    FILE* fp,
    std::vector<facebook::pdq::hashing::Hash256>& hashes) {
  char* line = nullptr;
  size_t linelen = 0;
  while ((ssize_t)(linelen = getline(&line, &linelen, fp)) != -1) {
    facebook::pdq::hashing::Hash256 hash =
        facebook::pdq::hashing::Hash256::fromLineOrDie(line, linelen);
    hashes.push_back(hash);
  }
}

} // namespace io
} // namespace pdq
} // namespace facebook
