// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#include <pdq/cpp/io/hashio.h>

#include <fstream>
#include <iostream>
#include <string>

#include <stdlib.h>
#include <string.h>

namespace facebook {
namespace pdq {
namespace io {

// ----------------------------------------------------------------
// See comments in header file
bool loadHashAndMetadataFromStream(
    std::istream& in,
    facebook::pdq::hashing::Hash256& hash,
    std::string& metadata,
    int counter) {
  const std::string prefix = "hash=";
  std::string line;

  if (!std::getline(in, line)) {
    return false;
  }

  // Chomp
  if (!line.empty() && line.back() == '\n') {
    line.pop_back();
  }

  // Split hash from metadata on comma
  size_t cut_pos = line.find(',');
  if (cut_pos == std::string::npos) {
    metadata = "idx=" + std::to_string(counter);
  } else {
    metadata = line.substr(cut_pos + 1);
    line = line.substr(0, cut_pos);
  }
  if (line.substr(0, prefix.size()) == prefix) {
    hash = facebook::pdq::hashing::Hash256::fromStringOrDie(
        line.substr(prefix.size()));
  } else {
    hash = facebook::pdq::hashing::Hash256::fromStringOrDie(line);
  }
  return true;
}

// ----------------------------------------------------------------
// See comments in header file
void loadHashesAndMetadataFromStream(
    std::istream& in,
    std::vector<std::pair<facebook::pdq::hashing::Hash256, std::string>>&
        vector_of_pairs) {
  while (true) {
    int counter = vector_of_pairs.size() + 1;
    facebook::pdq::hashing::Hash256 hash;
    std::string metadata;
    bool rc = loadHashAndMetadataFromStream(in, hash, metadata, counter);
    if (!rc) {
      break;
    }
    vector_of_pairs.push_back(std::make_pair(hash, metadata));
  }
}

// ----------------------------------------------------------------
bool loadHashesAndMetadataFromFile(
    const char* filename,
    std::vector<std::pair<facebook::pdq::hashing::Hash256, std::string>>&
        vector_of_pairs) {
  std::ifstream in(filename);
  if (!in) {
    perror("fopen");
    fprintf(stderr, "Could not open \"%s\" for read.\n", filename);
    return false;
  }
  loadHashesAndMetadataFromStream(in, vector_of_pairs);
  in.close();
  return true;
}

// ----------------------------------------------------------------
bool loadHashesAndMetadataFromFiles(
    char** filenames,
    int num_filenames,
    std::vector<std::pair<facebook::pdq::hashing::Hash256, std::string>>&
        vector_of_pairs) {
  if (num_filenames == 0) {
    loadHashesAndMetadataFromStream(std::cin, vector_of_pairs);
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
    loadHashesFromStream(std::cin, hashes);
  } else {
    for (int i = 0; i < num_filenames; i++) {
      loadHashesFromFileOrDie(filenames[i], hashes);
    }
  }
}

// ----------------------------------------------------------------
void loadHashesFromFileOrDie(
    const char* filename,
    std::vector<facebook::pdq::hashing::Hash256>& hashes) {
  if (!loadHashesFromFile(filename, hashes)) {
    // Error message already printed out
    exit(1);
  }
}

// ----------------------------------------------------------------
bool loadHashesFromFile(
    const char* filename,
    std::vector<facebook::pdq::hashing::Hash256>& hashes) {
  std::ifstream in(filename);
  if (!in) {
    perror("fopen");
    fprintf(stderr, "Could not open \"%s\" for read.\n", filename);
    return false;
  }
  loadHashesFromStream(in, hashes);
  in.close();
  return true;
}

// ----------------------------------------------------------------
void loadHashesFromStream(
    std::istream& in, std::vector<facebook::pdq::hashing::Hash256>& hashes) {
  std::string line;
  while (std::getline(in, line)) {
    facebook::pdq::hashing::Hash256 hash =
        facebook::pdq::hashing::Hash256::fromLineOrDie(line);
    hashes.push_back(hash);
  }
}

} // namespace io
} // namespace pdq
} // namespace facebook
