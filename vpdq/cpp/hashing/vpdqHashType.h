#include <pdq/cpp/common/pdqhashtypes.h>

#ifndef VPDQHASHTYPE_H
#define VPDQHASHTYPE_H

using namespace std;

namespace facebook {
namespace vpdq {
namespace hashing {

struct vpdqFeature {
  facebook::pdq::hashing::Hash256 pdqHash;
  int frameNumber;
  int quality;
};

} // namespace hashing
} // namespace vpdq
} // namespace facebook

#endif // VPDQHASHTYPE_H
