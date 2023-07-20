// ================================================================
// Copyright (c) Meta Platforms, Inc. and affiliates.
// ================================================================

#include <stdio.h>
extern "C" {
#include <libavcodec/avcodec.h>
#include <libavformat/avformat.h>
#include <libavutil/frame.h>
#include <libavutil/mem.h>
}

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

using namespace std;
using namespace facebook::pdq::hashing;
using namespace facebook::pdq::io;

namespace facebook {
namespace vpdq {
namespace io {

const int TIMESTAMP_OUTPUT_PRECISION = 3;
const int MILLISEC_IN_SEC = 1000000;

bool loadHashesFromFileOrDie(
    const string& inputHashFileName,
    vector<hashing::vpdqFeature>& pdqHashes,
    const char* programName) {
  std::ifstream inputfp(inputHashFileName);
  string str;
  if (!inputfp.is_open()) {
    fprintf(
        stderr,
        "%s: could not open \"%s\".\n",
        programName,
        inputHashFileName.c_str());
    return false;
  }

  while (getline(inputfp, str)) {
    vector<string> frameValues;
    stringstream ss(str);

    while (ss.good()) {
      string substr;
      getline(ss, substr, ',');
      frameValues.push_back(substr);
    }

    if (frameValues.size() != 4) {
      fprintf(
          stderr,
          "%s: Wrong format of Hash\"%s\".\n",
          programName,
          str.c_str());
      return false;
    }
    pdqHashes.push_back(
        {pdq::hashing::Hash256::fromStringOrDie(frameValues[2]),
         atoi(frameValues[0].c_str()),
         atoi(frameValues[1].c_str()),
         atof(frameValues[3].c_str())});
  }
  if (pdqHashes.size() == 0) {
    fprintf(
        stderr,
        "%s: Empty hash file \"%s\".\n",
        programName,
        inputHashFileName.c_str());
    return false;
  }
  return true;
}

bool outputVPDQFeatureToFile(
    const string& outputHashFileName,
    vector<hashing::vpdqFeature>& pdqHashes,
    const char* programName) {
  ofstream outputfp;
  outputfp.open(outputHashFileName.c_str());
  if (!outputfp.is_open()) {
    fprintf(
        stderr,
        "%s: could not open \"%s\".\n",
        programName,
        outputHashFileName.c_str());
    return false;
  }
  // write to output file
  for (auto s : pdqHashes) {
    outputfp << s.frameNumber;
    outputfp << ",";
    outputfp << s.quality;
    outputfp << ",";
    outputfp << s.pdqHash.format().c_str();
    outputfp << ",";
    outputfp << setprecision(TIMESTAMP_OUTPUT_PRECISION) << fixed
             << s.timeStamp;
    outputfp << "\n";
  }
  // close outputfile
  outputfp.close();
  return true;
}

} // namespace io
} // namespace vpdq
} // namespace facebook
