#ifndef VPDQIO_H
#define VPDQIO_H

#include <pdq/cpp/common/pdqhashtypes.h>
#include <vpdq/cpp/hashing/vpdqHashType.h>

using namespace std;

namespace facebook {
namespace vpdq {
namespace io {

bool loadHashesFromFileOrDie(
    const string& inputHashFileName,
    vector<hashing::vpdqFeature>& pdqHashes,
    const char* programName);
bool outputVPDQFeatureToFile(
    const string& outputHashFileName,
    vector<hashing::vpdqFeature>& pdqHashes,
    const char* programName);
bool readVideoStreamInfo(
    const string& inputVideoFileName,
    int& width,
    int& height,
    double& framesPerSec,
    const char* programName);
bool readVideoDuration(
    const string& inputVideoFileName,
    double& durationInSec,
    const char* programName);
} // namespace io
} // namespace vpdq
} // namespace facebook
#endif // VPDQIO_H
