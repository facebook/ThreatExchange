// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

extern "C" {
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavutil/frame.h>
#include <libavutil/mem.h>
}

#include <cstdio>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include <pdq/cpp/common/pdqhashtypes.h>
#include <pdq/cpp/io/hashio.h>
#include <vpdq/cpp/hashing/vpdqHashType.h>
#include <vpdq/cpp/io/vpdqio.h>

using namespace facebook::pdq::hashing;
using namespace facebook::pdq::io;

namespace facebook {
namespace vpdq {
namespace io {

const int TIMESTAMP_OUTPUT_PRECISION = 3;
const int MILLISEC_IN_SEC = 1000000;

bool loadHashesFromFileOrDie(
    const string& inputHashFileName,
    std::vector<hashing::vpdqFeature>& pdqHashes) {
  std::ifstream inputfp(inputHashFileName);
  if (!inputfp) {
    std::cerr << "Could not open input file " << inputHashFileName << std::endl;
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

    if (frameValues.size() != 4) {
      std::cerr << "Wrong format of hash: " << str << std::endl;
      return false;
    }
    pdqHashes.push_back(
        {pdq::hashing::Hash256::fromStringOrDie(frameValues[2]),
         std::atoi(frameValues[0].c_str()),
         std::atoi(frameValues[1].c_str()),
         std::atof(frameValues[3].c_str())});
  }
  if (pdqHashes.size() == 0) {
    std::cerr << "Empty hash file " << inputHashFileName << std::endl;
    return false;
  }
  return true;
}

bool outputVPDQFeatureToFile(
    const std::string& outputHashFileName,
    const std::vector<hashing::vpdqFeature>& pdqHashes) {
  std::ofstream outfile(outputHashFileName);
  if (!outfile) {
    std::cerr << "Could not open output file " << outputHashFileName
              << std::endl;
    return false;
  }

  // Write feature to output file
  for (const auto& s : pdqHashes) {
    outfile << s.frameNumber;
    outfile << ",";
    outfile << s.quality;
    outfile << ",";
    outfile << s.pdqHash.format().c_str();
    outfile << ",";
    outfile << std::setprecision(TIMESTAMP_OUTPUT_PRECISION) << std::fixed
            << s.timeStamp;
    outfile << "\n";
  }
  outfile.close();
  return true;
}

} // namespace io
} // namespace vpdq
} // namespace facebook
