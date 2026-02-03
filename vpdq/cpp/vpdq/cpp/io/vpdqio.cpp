// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#include <vpdq/cpp/io/vpdqio.h>

#include <pdq/cpp/common/pdqhashtypes.h>
#include <vpdq/cpp/hashing/vpdqHashType.h>

#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace facebook {
namespace vpdq {
namespace io {

static constexpr int TIMESTAMP_OUTPUT_PRECISION = 3;

bool loadHashesFromFileOrDie(
    const std::string& inputHashFileName,
    std::vector<facebook::vpdq::hashing::vpdqFeature>& vpdqHashes) {
  std::ifstream inputfp(inputHashFileName);
  if (!inputfp) {
    std::cerr << "Could not open input file " << inputHashFileName << '\n';
    return false;
  }

  std::string str;
  while (std::getline(inputfp, str)) {
    std::vector<std::string> frameValues;
    std::stringstream ss(str);

    while (ss.good()) {
      std::string substr;
      std::getline(ss, substr, ',');
      frameValues.push_back(substr);
    }

    if (frameValues.size() < 4U) {
      std::cerr << "Wrong format of hash: " << str << '\n';
      return false;
    }
    vpdqHashes.push_back(
        {facebook::pdq::hashing::Hash256::fromStringOrDie(frameValues[2]),
         std::stoi(frameValues[0]),
         std::stoi(frameValues[1]),
         std::stod(frameValues[3])});
  }
  if (vpdqHashes.empty()) {
    std::cerr << "Empty hash file " << inputHashFileName << '\n';
    return false;
  }
  return true;
}

bool outputVPDQFeatureToFile(
    const std::string& outputHashFileName,
    const std::vector<facebook::vpdq::hashing::vpdqFeature>& vpdqHashes) {
  std::ofstream outfile(outputHashFileName);
  if (!outfile) {
    std::cerr << "Could not open output file " << outputHashFileName << '\n';
    return false;
  }

  // Write feature to output file
  for (const auto& s : vpdqHashes) {
    outfile << s.frameNumber;
    outfile << ",";
    outfile << s.quality;
    outfile << ",";
    outfile << s.pdqHash.format();
    outfile << ",";
    outfile << std::setprecision(TIMESTAMP_OUTPUT_PRECISION) << std::fixed
            << s.timeStamp;
    outfile << "\n";
  }
  return true;
}

} // namespace io
} // namespace vpdq
} // namespace facebook
