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
    const char* argv0);

bool outputVPDQFeatureToFile(
    const string& outputHashFileName,
    vector<hashing::vpdqFeature>& pdqHashes,
    const char* argv0);
bool readVideoResolution(
    const string& inputVideoFileName,
    int& width,
    int& height,
    const char* argv0);
} // namespace io
} // namespace vpdq
} // namespace facebook
#endif // VPDQIO_H
