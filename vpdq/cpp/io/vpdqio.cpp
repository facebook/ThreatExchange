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
  ifstream inputfp(inputHashFileName);
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
        {pdq::hashing::Hash256::fromStringOrDie((char*)frameValues[2].c_str()),
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

bool readVideoStreamInfo(
    const string& inputVideoFileName,
    int& width,
    int& height,
    double& framesPerSec,
    const char* programName) {
  AVFormatContext* pFormatCtx = avformat_alloc_context();
  int rc =
      avformat_open_input(&pFormatCtx, inputVideoFileName.c_str(), NULL, NULL);
  if (rc != 0) {
    fprintf(
        stderr,
        "%s: could not open video \"%s\".\n",
        programName,
        inputVideoFileName.c_str());
    return false;
  }
  AVCodecContext* pCodecCtx;
  int videoStream = -1;
  rc = avformat_find_stream_info(pFormatCtx, NULL);
  if (rc < 0) {
    fprintf(
        stderr,
        "%s: could not find video stream info \"%s\".\n",
        programName,
        inputVideoFileName.c_str());
    return false;
  }
  for (int i = 0; i < pFormatCtx->nb_streams; i++) {
    if (pFormatCtx->streams[i]->codecpar->codec_type == AVMEDIA_TYPE_VIDEO &&
        videoStream < 0) {
      videoStream = i;
    }
  }
  if (videoStream == -1) {
    fprintf(
        stderr,
        "%s: could not find video stream \"%s\".\n",
        programName,
        inputVideoFileName.c_str());
    return false;
  }
  AVCodecParameters* videoParameter =
      pFormatCtx->streams[videoStream]->codecpar;
  height = videoParameter->height;
  width = videoParameter->width;
  AVRational fr = pFormatCtx->streams[videoStream]->avg_frame_rate;
  framesPerSec = (double)fr.num / (double)fr.den;
  return true;
}
// readVideoDuration is not used in calculating VPDQ for now
bool readVideoDuration(
    const string& inputVideoFileName,
    double& durationInSec,
    const char* programName) {
  AVFormatContext* pFormatCtx = avformat_alloc_context();
  int rc =
      avformat_open_input(&pFormatCtx, inputVideoFileName.c_str(), NULL, NULL);
  if (rc != 0) {
    fprintf(
        stderr,
        "%s: could not open video \"%s\".\n",
        programName,
        inputVideoFileName.c_str());
    return false;
  }
  durationInSec = (double)pFormatCtx->duration / MILLISEC_IN_SEC;
  return true;
}
} // namespace io
} // namespace vpdq
} // namespace facebook
